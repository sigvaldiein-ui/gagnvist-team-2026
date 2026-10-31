"""General retrieval behavior on synthetic topics, never the competition questions."""

from dataclasses import replace

import numpy as np
import pytest

from gagnvist.config import ConfigError, load_settings
from gagnvist.search.hybrid import BM25, HybridRetriever, RetrievalConfig, query_parts, tokens
from gagnvist.search.vector_search import Card, VectorIndex


class Client:
    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.extend(texts)
        return np.array([[1.0, 0.0] for _ in texts], dtype=np.float32)


def index():
    return VectorIndex(
        [
            Card("Environment/en/trees/A", "en", "Forest cover. Region, Year"),
            Card("Environment/en/rivers/B", "en", "River flow. Station, Year"),
            Card("Environment/is/skogar/C", "is", "Skógar. Svæði, Ár"),
        ],
        np.array([[1.0, 0.0], [0.9, 0.1], [1.0, 0.0]], dtype=np.float32),
        "synthetic",
    )


def test_lexical_can_recover_different_topic_without_model_call():
    client = Client()
    retriever = HybridRetriever(index(), RetrievalConfig(mode="lexical", decompose=False))
    result = retriever.search("river flow", "en", client)
    assert result[0].card.folder.endswith("/B")
    assert client.calls == []
    assert result[0].signals[0].source == "bm25"


def test_dense_ablation_exactly_preserves_shipped_search_order_and_scores():
    vectors = index()
    client = Client()
    result = HybridRetriever(vectors, RetrievalConfig(mode="dense", decompose=False)).search(
        "river flow", "en", client
    )
    expected = vectors.search(np.array([1.0, 0.0], dtype=np.float32), language="en", limit=100)
    assert result == expected


def test_no_cross_language_results_and_no_keyword_hits_are_not_invented():
    client = Client()
    retriever = HybridRetriever(index(), RetrievalConfig(mode="lexical"))
    assert retriever.search("river flow", "is", client) == []
    assert retriever.search("river flow", "unknown", client) == []


def test_rrf_formula_and_repeated_queries_are_deterministic():
    client = Client()
    config = RetrievalConfig(decompose=False)
    retriever = HybridRetriever(index(), config)
    first = retriever.search("river flow", "en", client)
    assert first == retriever.search("river flow", "en", client)
    for match in first:
        assert match.score == sum(s.rrf for s in match.signals)
        for signal in match.signals:
            assert signal.rrf == pytest.approx(1 / (config.rrf_k + signal.rank))
    assert len({m.card.folder for m in first}) == len(first)


def test_stable_folder_tie_breaking_and_zero_weight_channel():
    tied = VectorIndex(
        [
            Card("Environment/en/zebra/Z", "en", "River flow. Year"),
            Card("Environment/en/birch/Y", "en", "River flow. Year"),
        ],
        np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32),
        "synthetic",
    )
    retriever = HybridRetriever(tied, RetrievalConfig(dense_weight=0, decompose=False))
    result = retriever.search("year", "en", Client())
    assert [m.card.folder for m in result] == sorted(m.card.folder for m in result)
    assert all(s.source == "bm25" for m in result for s in m.signals)


def test_subqueries_are_bounded_general_and_keep_full_question():
    question = "Forest cover and river flow; soil quality and rainfall"
    result = query_parts(question, 2)
    assert result == [question, "Forest cover", "river flow"]
    assert query_parts(question, 0) == [question]
    assert query_parts("change between 2010 and 2015") == [
        "change between 2010 and 2015",
        "change between 2010",
    ]
    assert query_parts("Skógar og ár", 3)[0] == "Skógar og ár"


def test_unicode_normalization_and_underscore_folder_tokens():
    assert tokens("Sko\u0301gar/FOREST_cover") == ["skógar", "forest", "cover"]
    assert tokens("the forest and river") == ["forest", "river"]


def test_subquery_weight_budget_and_trace_are_preserved():
    retriever = HybridRetriever(index())
    result = retriever.search("forest cover and river flow", "en", Client())
    assert result
    assert any(s.query == "river flow" for m in result for s in m.signals)
    for m in result:
        for s in m.signals:
            weight = 1 if s.query == "forest cover and river flow" else 0.25
            assert s.rrf == pytest.approx(weight / (60 + s.rank))


@pytest.mark.parametrize(
    "changes",
    [
        {"candidate_limit": 0},
        {"candidate_limit": 101},
        {"candidate_limit": True},
        {"mode": "rerank"},
        {"dense_weight": -1},
        {"lexical_weight": float("nan")},
        {"rrf_k": 0},
        {"bm25_b": 1.1},
        {"max_subqueries": 4},
        {"decompose": "true"},
        {"dense_weight": 0, "lexical_weight": 0},
    ],
)
def test_invalid_configuration_fails_closed(changes):
    with pytest.raises(ValueError):
        replace(RetrievalConfig(), **changes)


def test_bm25_empty_corpus_and_repeated_query_words():
    assert BM25([], 1.2, 0.75).search("forest", 100) == []
    bm25 = BM25([("a", "forest cover"), ("b", "river flow")], 1.2, 0.75)
    assert bm25.search("forest", 100) == bm25.search("forest forest", 100)


def test_settings_activate_hybrid_and_allow_dense_ablation(tmp_path):
    from conftest import SHARED_SETTINGS

    path = tmp_path / "gagnvist.toml"
    text = SHARED_SETTINGS.read_text()
    path.write_text(text)
    assert load_settings(path).retrieval.mode == "hybrid"
    path.write_text(text.replace('mode = "hybrid"', 'mode = "dense"'))
    assert load_settings(path).retrieval.mode == "dense"
    path.write_text(text.replace("candidate_limit = 100", "candidate_limit = 0"))
    with pytest.raises(ConfigError):
        load_settings(path)


def test_candidate_union_is_capped_at_one_hundred():
    cards = [Card(f"Synthetic/en/topic/{i:04}", "en", "Forest river") for i in range(150)]
    vectors = np.tile(np.array([[1.0, 0.0]], dtype=np.float32), (150, 1))
    retriever = HybridRetriever(VectorIndex(cards, vectors, "synthetic"))
    matches = retriever.search("forest and river", "en", Client(), limit=1000)
    assert len(matches) == 100
    assert len({m.card.folder for m in matches}) == 100
    assert all(s.rank <= 100 for m in matches for s in m.signals)


def test_configured_pipeline_uses_hybrid_signals_but_still_one_source(
    data_folder, table_database, standin_client
):
    from gagnvist.answering.pipeline import Pipeline
    from gagnvist.search.table_index import TableIndex
    from gagnvist.search.vector_search import make_cards

    tables = TableIndex(table_database)
    vectors = VectorIndex.build(make_cards(tables), standin_client.embed, "standin-embeddings")
    with Pipeline(
        data_folder, tables, vectors, standin_client, retrieval_config=RetrievalConfig()
    ) as pipeline:
        answer = pipeline.answer("Results of the presidential election 1980: valid votes")
        assert answer.candidates
        assert answer.candidates[0].signals
        assert answer.table.folder == answer.candidates[0].card.folder
        assert answer.extra_tables == ()
