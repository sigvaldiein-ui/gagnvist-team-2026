"""Synthetic conformance examples; no competition answers or closed-test data."""

from dataclasses import replace

import numpy as np
import pytest

from gagnvist.data.catalogue import Category, Dimension, TableMetadata
from gagnvist.search.hybrid import HybridRetriever, RetrievalConfig
from gagnvist.search.rerank import (
    CONFLICT,
    MATCH,
    UNKNOWN,
    Candidate,
    MetadataReranker,
    Period,
    content_terms,
    order_candidates,
    requested_periods,
    temporal_state,
)
from gagnvist.search.table_index import TableIndex
from gagnvist.search.vector_search import Card, Match, RerankSignal, VectorIndex


def candidate(
    name,
    rank,
    state=UNKNOWN,
    score=1,
    dims=2,
    complete=True,
    updated="2020-01-01",
    equivalence=None,
):
    match = Match(Card("Synthetic/en/" + name, "en", "Forest"), 1 / rank)
    evidence = RerankSignal(rank, state, score, (), dims, complete, (), ())
    return Candidate(match, evidence, updated, equivalence)


def names(rows):
    return [c.match.card.folder.rsplit("/", 1)[-1] for c in rows]


def metadata(*values, complete=True):
    return TableMetadata(
        "Forest",
        (
            Dimension(
                "time", "Year", tuple(Category(v, v if complete else "") for v in values), True
            ),
        ),
    )


def test_only_conflict_has_absolute_bucket_priority_and_no_match_bonus():
    rows = [
        candidate("conflict", 1, CONFLICT, score=100),
        candidate("unknown", 2, UNKNOWN, score=15),
        candidate("match", 3, MATCH, score=0),
    ]
    assert names(order_candidates(rows)) == ["unknown", "match", "conflict"]
    rows = [candidate("unknown", 1), candidate("match", 2, MATCH)]
    assert names(order_candidates(rows)) == ["unknown", "match"]


@pytest.mark.parametrize("state", [UNKNOWN, CONFLICT])
@pytest.mark.parametrize("score", [0, 15])
def test_whole_unknown_or_conflict_tie_group_preserves_source_rank(state, score):
    rows = [
        candidate("A", 1, state, score, dims=9),
        candidate("B", 2, state, score, dims=0, updated="2030-01-01", equivalence="certified"),
    ]
    assert names(order_candidates(rows)) == ["A", "B"]


def test_one_incomplete_or_unknown_candidate_freezes_entire_equal_score_group():
    rows = [
        candidate("A", 1, MATCH, dims=9),
        candidate("B", 2, MATCH, dims=1),
        candidate("C", 3, MATCH, dims=0, complete=False),
    ]
    assert names(order_candidates(rows)) == ["A", "B", "C"]
    rows[2] = candidate("C", 3, UNKNOWN, dims=0)
    assert names(order_candidates(rows)) == ["A", "B", "C"]


def test_all_match_complete_group_can_use_dimensions_then_certified_dates():
    rows = [
        candidate("A", 1, MATCH, dims=9),
        candidate("B", 2, MATCH, dims=1, updated="2020-01-01", equivalence="verified"),
        candidate("C", 3, MATCH, dims=1, updated="2021-01-01", equivalence="verified"),
    ]
    assert names(order_candidates(rows)) == ["C", "B", "A"]


def test_no_equivalence_no_date_priority_and_missing_date_preserves_run():
    rows = [candidate("A", 1, MATCH), candidate("B", 2, MATCH, updated="2030-01-01")]
    assert names(order_candidates(rows)) == ["A", "B"]
    rows = [
        replace(rows[0], updated="", equivalence="verified"),
        replace(rows[1], equivalence="verified"),
    ]
    assert names(order_candidates(rows)) == ["A", "B"]


def test_date_never_jumps_across_uncertified_peer():
    rows = [
        candidate("A", 1, MATCH, equivalence="verified"),
        candidate("B", 2, MATCH),
        candidate("C", 3, MATCH, updated="2030-01-01", equivalence="verified"),
    ]
    assert names(order_candidates(rows)) == ["A", "B", "C"]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("2026Q2", (Period(2026, "quarter", 2),)),
        ("2026Á2", (Period(2026, "quarter", 2),)),
        ("2. ársfjórðungur 2026", (Period(2026, "quarter", 2),)),
        ("2026M09", (Period(2026, "month", 9),)),
        ("September 2026", (Period(2026, "month", 9),)),
        ("1. janúar 2026", (Period(2026, "month", 1),)),
        ("2019\u20132021", (Period(2019), Period(2020), Period(2021))),
        ("latest year", ()),
    ],
)
def test_explicit_calendar_parser(text, expected):
    assert requested_periods(text) == expected


def test_actual_values_not_min_max_bounds_define_coverage():
    meta = metadata("2019", "2021")
    assert temporal_state((Period(2020),), meta)[0] == CONFLICT
    assert temporal_state((Period(2019),), meta)[0] == MATCH
    assert temporal_state((), meta)[0] == UNKNOWN
    assert temporal_state((Period(2020),), None)[0] == UNKNOWN
    assert temporal_state((Period(2020),), metadata("2019", "unrecognized"))[0] == UNKNOWN
    assert temporal_state((Period(2020, "quarter", 1),), meta)[0] == UNKNOWN


def test_quarter_aliases_and_inconsistent_code_label_are_conservative():
    assert temporal_state((Period(2026, "quarter", 2),), metadata("2026Á2"))[0] == MATCH
    bad = TableMetadata("Forest", (Dimension("time", "Year", (Category("2020", "2021"),), True),))
    assert temporal_state((Period(2020),), bad)[0] == UNKNOWN


@pytest.mark.parametrize(
    "language,left,right,hit",
    [
        ("is", "skógrækt", "skógræktar", True),
        ("is", "skógrækt", "sko\u0301græktar", True),
        ("is", "fæðingar", "fæddust", False),
        ("is", "ár", "árleg", False),
        ("is", "atvinnuleysi", "atvinnugrein", True),
        ("en", "forestry", "forested", False),
        ("en", "FOREST", "forest", True),
        ("en", "rivers", "river", False),
        ("en", "habitat", "habitats", False),
        ("en", "rainfall", "rainfall", True),
    ],
)
def test_ten_open_word_pairs_document_prefix_limits(language, left, right, hit):
    assert bool(content_terms(left, language) & content_terms(right, language)) == hit


def test_content_count_has_no_frequency_or_date_bonus():
    assert content_terms("the forest forest 2020", "en") == {"forest"}


def test_top10_membership_tail_and_original_scores_preserved(table_database):
    with_tables = TableIndex(table_database)
    try:
        entry = with_tables.entries()[0]
        matches = [Match(Card(entry.folder, entry.language, entry.title), 0.75)]
        matches += [Match(Card(f"Missing/en/{n}", "en", "forest"), 0.5) for n in range(12)]
        reranker = MetadataReranker(with_tables)
        result = reranker.rerank("forest", "en", matches)
        assert {m.card.folder for m in result[:10]} == {m.card.folder for m in matches[:10]}
        assert result[10:] == matches[10:]
        assert result[0].rerank is not None
        assert all(m.rerank is None for m in result[10:])
        assert {m.card.folder: m.score for m in result} == {m.card.folder: m.score for m in matches}
        assert reranker.rerank("forest", "en", matches) == result
    finally:
        with_tables.close()


def test_category_values_contribute_once_and_missing_data_never_bonus(table_database):
    tables = TableIndex(table_database)
    try:
        entry = tables.entries()[0]
        meta = tables.metadata(entry.folder)
        word = next(
            t for d in meta.dimensions for c in d.categories for t in content_terms(c.label, "en")
        )
        match = Match(Card(entry.folder, entry.language, entry.title), 1.0)
        result = MetadataReranker(tables).rerank(word + " " + word, "en", [match])
        assert result[0].rerank.word_count == 1
        missing = Match(Card("Missing/en/test", "en", word), 1.0)
        result = MetadataReranker(tables).rerank(word, "en", [missing])
        assert result[0].rerank.word_count == 0
        assert not result[0].rerank.complete_categories
    finally:
        tables.close()


def test_english_lexical_prefix_disabled_but_icelandic_enabled():
    cards = [Card("Topic/en/A", "en", "Forested"), Card("Topic/is/A", "is", "Skógrækt")]
    index = VectorIndex(cards, np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32), "synthetic")
    retriever = HybridRetriever(index, RetrievalConfig(mode="lexical"))
    assert retriever.lexical["en"].search("forestry", 10) == []
    assert retriever.lexical["is"].search("skógræktar", 10)
