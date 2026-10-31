"""General metadata BM25 with lexical-first interleaving or legacy RRF (no answer labels).

Documents are shipped card text (title and dimension labels) plus folder tokens.
No period/metric reranking, category selection, calculations or multi-table answers.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gagnvist.search.vector_search import Match, RetrievalSignal, VectorIndex

if TYPE_CHECKING:
    from gagnvist.models.client import ModelClient


@dataclass(frozen=True)
class RetrievalConfig:
    mode: str = "hybrid"
    candidate_limit: int = 100
    dense_weight: float = 1.0
    lexical_weight: float = 1.0
    rrf_k: float = 60.0
    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    decompose: bool = False
    fusion: str = "interleave"
    prefix: bool = True
    prefix_language: str = "is"
    rerank: bool = True
    max_subqueries: int = 3
    subquery_weight: float = 0.5

    def __post_init__(self) -> None:
        if self.mode not in {"dense", "lexical", "hybrid"}:
            raise ValueError("retrieval mode must be dense, lexical or hybrid")
        if type(self.candidate_limit) is not int or not 1 <= self.candidate_limit <= 100:
            raise ValueError("candidate_limit must be an integer from 1 to 100")
        if type(self.max_subqueries) is not int or not 0 <= self.max_subqueries <= 3:
            raise ValueError("max_subqueries must be an integer from 0 to 3")
        if self.prefix_language not in {"is", "all"}:
            raise ValueError("prefix_language must be is or all (legacy ablation)")
        if type(self.rerank) is not bool:
            raise ValueError("rerank must be boolean")
        if self.fusion not in {"rrf", "interleave"}:
            raise ValueError("fusion must be rrf or interleave")
        if type(self.prefix) is not bool:
            raise ValueError("prefix must be boolean")
        if type(self.decompose) is not bool:
            raise ValueError("decompose must be boolean")
        values = (
            self.dense_weight,
            self.lexical_weight,
            self.rrf_k,
            self.bm25_k1,
            self.bm25_b,
            self.subquery_weight,
        )
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError("retrieval weights must be finite numbers")
        if min(self.dense_weight, self.lexical_weight, self.subquery_weight) < 0:
            raise ValueError("retrieval weights cannot be negative")
        if self.dense_weight + self.lexical_weight <= 0:
            raise ValueError("at least one fusion weight must be positive")
        if self.rrf_k <= 0 or self.bm25_k1 <= 0 or not 0 <= self.bm25_b <= 1:
            raise ValueError("rrf_k and bm25_k1 must be positive; bm25_b must be 0..1")


# Closed-class grammatical words only. No subject nouns, table identifiers or synonyms.
_STOP_TEXT = """a an and are as at be by did do does for from had has have how in
is it its of on or that the their there these this to was were what when where which
who with að af á eða en er eru eftir fyrir frá hafði hafa hefur hvað hvar hve hver
hvernig hversu í með og sem til um var voru við þann það þess þetta þessi"""
_STOP = frozenset(_STOP_TEXT.split())
_COORDINATION = re.compile(r"\b(?:and|og)\b|;", re.IGNORECASE)


def tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).casefold()
    return [t for t in re.findall(r"[^\W_]+", text) if t not in _STOP]


def query_parts(question: str, maximum: int = 3) -> list[str]:
    """Keep full question, then distinct conjunction clauses with content words.

    Deliberately not a semantic planner: no domain lists or inferred missing context.
    Numeric-only clauses (e.g. the second year of 'between X and Y') are ignored.
    """
    full = unicodedata.normalize("NFC", question).strip()
    parts = [full]
    clauses = _COORDINATION.split(full)
    if len(clauses) == 1 or maximum <= 0:
        return parts
    seen = {tuple(tokens(full))}
    for clause in clauses:
        clause = clause.strip(" ,;?\t\n")
        key = tuple(tokens(clause))
        if key and any(any(c.isalpha() for c in t) for t in key) and key not in seen:
            parts.append(clause)
            seen.add(key)
        if len(parts) >= maximum + 1:
            break
    return parts


class BM25:
    def __init__(
        self, documents: Sequence[tuple[str, str]], k1: float, b: float, *, prefix: bool = False
    ) -> None:
        self.k1, self.b = k1, b
        self.prefix = prefix
        self.lengths: dict[str, int] = {}
        self.postings: dict[str, dict[str, int]] = defaultdict(dict)
        for folder, text in documents:
            counts = Counter(self.terms(text))
            self.lengths[folder] = sum(counts.values())
            for term, frequency in counts.items():
                self.postings[term][folder] = frequency
        self.average = sum(self.lengths.values()) / len(documents) if documents else 1.0
        self.average = self.average or 1.0

    def terms(self, text: str) -> list[str]:
        """Six Unicode characters for alphabetic terms; short/numeric terms stay exact."""
        return [term[:6] if self.prefix and term.isalpha() else term for term in tokens(text)]

    def search(self, query: str, limit: int) -> list[tuple[str, float]]:
        scores: dict[str, float] = defaultdict(float)
        n = len(self.lengths)
        for term in sorted(set(self.terms(query))):
            hits = self.postings.get(term, {})
            idf = math.log(1 + (n - len(hits) + 0.5) / (len(hits) + 0.5))
            for folder, frequency in hits.items():
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * self.lengths[folder] / self.average
                )
                scores[folder] += idf * frequency * (self.k1 + 1) / denominator
        return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]


class HybridRetriever:
    def __init__(self, index: VectorIndex, config: RetrievalConfig | None = None) -> None:
        config = config or RetrievalConfig()
        self.index = index
        self.config = config
        self.cards = {card.folder: card for card in index.cards}
        if len(self.cards) != len(index.cards):
            raise ValueError("retrieval card folders must be unique")
        self.lexical = {
            language: BM25(
                [
                    (c.folder, c.text + " " + c.folder)
                    for c in index.cards
                    if c.language == language
                ],
                config.bm25_k1,
                config.bm25_b,
                prefix=config.prefix and (language == "is" or config.prefix_language == "all"),
            )
            for language in {c.language for c in index.cards}
        }

    def search(
        self, question: str, language: str, client: ModelClient, *, limit: int = 100
    ) -> list[Match]:
        if limit < 1:
            raise ValueError("retrieval limit must be positive")
        if language not in self.lexical:
            return []
        cfg = self.config
        queries = query_parts(question, cfg.max_subqueries) if cfg.decompose else [question]
        queries = queries[: cfg.max_subqueries + 1]
        signals: dict[str, list[RetrievalSignal]] = defaultdict(list)
        # Dense-only is an exact ablation of shipped ranking: retain cosine/ties.
        if cfg.mode == "dense" and not cfg.decompose:
            return self.index.search(
                client.embed([question])[0],
                limit=min(limit, cfg.candidate_limit),
                language=language,
            )
        channel_lists: list[list[tuple[str, float]]] = []
        for number, query in enumerate(queries):
            weight = 1.0 if number == 0 else cfg.subquery_weight / max(1, len(queries) - 1)
            lists: list[tuple[str, float, list[tuple[str, float]]]] = []
            if cfg.mode != "lexical" and cfg.dense_weight > 0:
                dense = self.index.search(
                    client.embed([query])[0], limit=cfg.candidate_limit, language=language
                )
                lists.append(("dense", cfg.dense_weight, [(m.card.folder, m.score) for m in dense]))
            if cfg.mode != "dense" and cfg.lexical_weight > 0:
                lists.append(
                    (
                        "bm25",
                        cfg.lexical_weight,
                        self.lexical[language].search(query, cfg.candidate_limit),
                    )
                )
            # Lexical first, dense second, for each query. Full query comes first.
            lists.sort(key=lambda item: item[0] != "bm25")
            channel_lists.extend(matches for _, _, matches in lists)
            for source, source_weight, matches in lists:
                for rank, (folder, score) in enumerate(matches, 1):
                    contribution = (
                        weight * source_weight / (cfg.rrf_k + rank) if cfg.fusion == "rrf" else 0.0
                    )
                    if contribution or cfg.fusion == "interleave":
                        signals[folder].append(
                            RetrievalSignal(query, source, rank, score, contribution)
                        )
        if cfg.fusion == "interleave":
            # Round-robin positions; duplicates consume their slot, never another result.
            ordered = []
            seen: set[str] = set()
            for position in range(max((len(items) for items in channel_lists), default=0)):
                for items in channel_lists:
                    if position < len(items):
                        folder = items[position][0]
                        if folder not in seen:
                            ordered.append(folder)
                            seen.add(folder)
        else:
            ordered = sorted(signals, key=lambda f: (-sum(s.rrf for s in signals[f]), f))
        return [
            Match(
                self.cards[f],
                1.0 / rank if cfg.fusion == "interleave" else sum(s.rrf for s in signals[f]),
                tuple(signals[f]),
            )
            for rank, f in enumerate(ordered[: min(limit, cfg.candidate_limit)], 1)
        ]
