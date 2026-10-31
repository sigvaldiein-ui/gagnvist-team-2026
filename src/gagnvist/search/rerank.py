"""Kidda's four-stage metadata contract. No answer keys, model calls or cell reads."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from itertools import groupby

from gagnvist.data.catalogue import TableMetadata
from gagnvist.search.hybrid import tokens
from gagnvist.search.table_index import TableIndex
from gagnvist.search.vector_search import Match, RerankSignal

MATCH = "VERIFIED_MATCH"
CONFLICT = "VERIFIED_CONFLICT"
UNKNOWN = "UNKNOWN"

# Calendar vocabulary, not subject-specific synonyms or question identifiers.
_MONTH_NAMES = (
    ("january", "janúar"),
    ("february", "febrúar"),
    ("march", "mars"),
    ("april", "apríl"),
    ("may", "maí"),
    ("june", "júní"),
    ("july", "júlí"),
    ("august", "ágúst"),
    ("september", "september"),
    ("october", "október"),
    ("november", "nóvember"),
    ("december", "desember"),
)
_MONTHS = {name: n for n, names in enumerate(_MONTH_NAMES, 1) for name in names}
_YEAR = r"(?:19|20|21)\d{2}"


@dataclass(frozen=True, order=True)
class Period:
    year: int
    kind: str = "year"
    part: int = 0

    def text(self) -> str:
        return (
            str(self.year)
            + ({"year": "", "month": f"M{self.part:02}", "quarter": f"Q{self.part}"}[self.kind])
        )


def requested_periods(text: str) -> tuple[Period, ...]:
    """Explicit calendar periods only. Relative dates are deliberately unknown."""
    text = " ".join(text.casefold().split())
    specific: set[Period] = set()
    for year, kind, part in re.findall(rf"\b({_YEAR})\s*([mqá])\s*(\d{{1,2}})\b", text):
        number = int(part)
        if (kind == "m" and 1 <= number <= 12) or (kind != "m" and 1 <= number <= 4):
            specific.add(Period(int(year), "month" if kind == "m" else "quarter", number))
    for name, month in _MONTHS.items():
        for year in re.findall(rf"\b{name}\s+({_YEAR})\b", text):
            specific.add(Period(int(year), "month", month))
    # Both word orders are common; the optional ordinal dot is punctuation only.
    quarter_word = r"(?:quarter|ársfjórðung\w*)"
    for number, year in re.findall(rf"\b([1-4])\.?\s*{quarter_word}\s+({_YEAR})\b", text):
        specific.add(Period(int(year), "quarter", int(number)))
    for year, number in re.findall(rf"\b({_YEAR})\s+{quarter_word}\s*([1-4])\b", text):
        specific.add(Period(int(year), "quarter", int(number)))
    years = {int(y) for y in re.findall(rf"\b({_YEAR})\b", text)}
    # Explicit bounded ranges require every intervening year, not just endpoints.
    for first, last in re.findall(rf"\b({_YEAR})\s*[\u2013-]\s*({_YEAR})\b", text):
        if 0 <= int(last) - int(first) <= 100:
            years.update(range(int(first), int(last) + 1))
    years.difference_update(p.year for p in specific)
    return tuple(sorted(specific | {Period(y) for y in years}))


def content_terms(text: str, language: str) -> frozenset[str]:
    """Distinct alphabetic content tokens; numeric dates are not word bonuses."""
    return frozenset(t[:6] if language == "is" else t for t in tokens(text) if t.isalpha())


def category_period(code: str, label: str) -> Period | None:
    def one(value: str) -> Period | None:
        value = value.strip().casefold()
        if re.fullmatch(_YEAR, value):
            return Period(int(value))
        match = re.fullmatch(rf"({_YEAR})([mqá])(\d{{1,2}})", value)
        if match:
            year, kind, part = match.groups()
            n = int(part)
            if (kind == "m" and 1 <= n <= 12) or (kind != "m" and 1 <= n <= 4):
                return Period(int(year), "month" if kind == "m" else "quarter", n)
        parsed = requested_periods(value)
        # A label must itself identify just one supported period, not an interval.
        if len(parsed) == 1 and any(name in value for name in _MONTHS):
            return parsed[0]
        return None

    a, b = one(code), one(label)
    if a is not None and b is not None and a != b:
        return None
    return a or b


def temporal_state(
    requested: tuple[Period, ...], metadata: TableMetadata | None
) -> tuple[str, tuple[str, ...]]:
    if not requested or metadata is None:
        return UNKNOWN, ()
    states: list[str] = []
    available: set[str] = set()
    for dimension in metadata.dimensions:
        if not dimension.is_time:
            continue
        parsed = [category_period(c.code, c.label) for c in dimension.categories]
        known = {p for p in parsed if p is not None}
        available.update(p.text() for p in known)
        if set(requested) <= known:
            states.append(MATCH)
        elif (
            parsed
            and all(p is not None for p in parsed)
            and len({p.kind for p in known} | {p.kind for p in requested}) == 1
        ):
            states.append(CONFLICT)
        else:
            states.append(UNKNOWN)
    state = (
        MATCH
        if MATCH in states
        else CONFLICT
        if states and all(s == CONFLICT for s in states)
        else UNKNOWN
    )
    return state, tuple(sorted(available))


@dataclass(frozen=True)
class Candidate:
    match: Match
    evidence: RerankSignal
    updated: str
    equivalence: str | None = None


def _date(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(UTC).replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError:
        return None


def order_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Stable bucket/count sort, then whole-group eligibility, never per-row fallback."""
    ordered = sorted(
        candidates,
        key=lambda c: (
            c.evidence.temporal_state == CONFLICT,
            -c.evidence.word_count,
            c.evidence.source_rank,
        ),
    )
    result: list[Candidate] = []
    for _, values in groupby(
        ordered, key=lambda c: (c.evidence.temporal_state == CONFLICT, c.evidence.word_count)
    ):
        group = list(values)
        eligible = all(
            c.evidence.temporal_state == MATCH and c.evidence.complete_categories for c in group
        )
        if not eligible:
            result.extend(group)
            continue
        group.sort(key=lambda c: c.evidence.unmatched_dimensions)
        # Dates only reorder contiguous, externally certified equivalent peers with
        # the same dimension count; never jump across an uncertified table.
        for _, peers in groupby(
            group, key=lambda c: (c.evidence.unmatched_dimensions, c.equivalence)
        ):
            run = list(peers)
            dates = [_date(c.updated) for c in run]
            if run[0].equivalence is not None and all(d is not None for d in dates):
                run.sort(key=lambda c: _date(c.updated) or datetime.min, reverse=True)
            result.extend(run)
    return result


class MetadataReranker:
    """Top-10 only. Metadata comes read-only from the existing SQLite index."""

    def __init__(
        self, tables: TableIndex, *, verified_equivalence: dict[str, str] | None = None
    ) -> None:
        self.tables = tables
        # No inference from table code, title or expected answers. With no supplied
        # adjudication records this remains empty and date tie-breaks are inactive.
        self.verified_equivalence = verified_equivalence or {}
        self.cache: dict[str, tuple[str, str, TableMetadata | None]] = {}

    def rerank(self, question: str, language: str, matches: list[Match]) -> list[Match]:
        terms = content_terms(question, language)
        periods = requested_periods(question)
        candidates: list[Candidate] = []
        for rank, match in enumerate(matches[:10], 1):
            folder = match.card.folder
            if folder not in self.cache:
                try:
                    entry = self.tables.entry(folder)
                    self.cache[folder] = (
                        entry.title,
                        entry.last_updated,
                        self.tables.metadata(folder),
                    )
                except KeyError:
                    self.cache[folder] = ("", "", None)
            title, updated, metadata = self.cache[folder]
            dimension_terms = (
                []
                if metadata is None
                else [
                    content_terms(" ".join([d.label, *(c.label for c in d.categories)]), language)
                    for d in metadata.dimensions
                ]
            )
            document = content_terms(title, language).union(*dimension_terms)
            matched = tuple(sorted(terms & document))
            complete = (
                metadata is not None
                and bool(metadata.dimensions)
                and all(
                    d.code
                    and d.label
                    and d.categories
                    and all(c.code and c.label for c in d.categories)
                    for d in metadata.dimensions
                )
            )
            unmatched = (
                0
                if metadata is None
                else sum(
                    not (terms & ts) and not (d.is_time and periods)
                    for d, ts in zip(metadata.dimensions, dimension_terms, strict=True)
                )
            )
            state, available = temporal_state(periods, metadata)
            evidence = RerankSignal(
                rank,
                state,
                len(matched),
                matched,
                unmatched,
                complete,
                tuple(p.text() for p in periods),
                available,
            )
            candidates.append(
                Candidate(match, evidence, updated, self.verified_equivalence.get(folder))
            )
        ranked = order_candidates(candidates)
        return [replace(c.match, rerank=c.evidence) for c in ranked] + matches[10:]
