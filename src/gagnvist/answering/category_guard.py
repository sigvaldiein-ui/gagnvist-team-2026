"""Conservative total-category correction, separate from frozen retrieval.

The model must explicitly mark a dimension unspecified. Missing/uncertain scope,
time/measure dimensions and lexical evidence of a requested category all veto a
correction. A total must be unique; no category is synthesized.
"""

from __future__ import annotations

from collections.abc import Mapping

from gagnvist.answering.choose_categories import Choice, is_total, looks_like_time
from gagnvist.data.catalogue import Dimension, TableMetadata
from gagnvist.models.prompts import _same_word, _words

_MEASURES = {
    "unit",
    "units",
    "measure",
    "metric",
    "item",
    "indicator",
    "contents",
    "eining",
    "einingar",
    "maelistard",
    "maelistaerd",
    "visitala",
    "stard",
    "tegund",
    "type",
    "lidhur",
    "lidur",
    "fjardaed",
    "fjarhaed",
}


def is_measure(dimension: Dimension) -> bool:
    return bool(_words(dimension.code + " " + dimension.label) & _MEASURES)


def guard_totals(question: str, metadata: TableMetadata, choice: Choice, scopes: object) -> Choice:
    selection = {code: list(values) for code, values in choice.selection.items()}
    notes = list(choice.notes)
    if not isinstance(scopes, Mapping):
        return choice
    asked = _words(question)
    for dimension in metadata.dimensions:
        if scopes.get(dimension.code) != "unspecified":
            continue
        if looks_like_time(dimension) or is_measure(dimension):
            continue
        # Use the existing category-label matcher; never tune the search/parser here.
        if any(
            _same_word(a, w)
            for category in dimension.categories
            if not is_total(category)
            for w in _words(category.label)
            for a in asked
        ):
            notes.append(f"{dimension.code}: total guard vetoed by category evidence")
            continue
        totals = {c.code: c for c in dimension.categories if is_total(c)}
        if len(totals) != 1:
            notes.append(f"{dimension.code}: total guard abstained; no unique total")
            continue
        total = next(iter(totals.values()))
        if selection[dimension.code] != [total.code]:
            selection[dimension.code] = [total.code]
            notes.append(f"{dimension.code}: unspecified dimension, guarded total {total.label!r}")
    return Choice(selection, notes)
