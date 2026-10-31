"""Step 3: read the chosen numbers from the table's data file.

No model is involved: every number comes straight from the table's ``data.px``, so the
numbers in an answer are exactly the ones Statistics Iceland published.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path

from gagnvist.answering.choose_categories import Selection
from gagnvist.data.catalogue import CatalogueEntry, Category, Dimension, TableMetadata
from gagnvist.data.px_reader import (
    MARKERS,
    Cell,
    PxError,
    PxFile,
    _items,
    _parse_statements,
    _read_header,
)


@dataclass(frozen=True)
class Fact:
    """One number of a table and the categories it belongs to."""

    categories: tuple[tuple[Dimension, Category], ...]  # one per dimension, in table order
    cell: Cell
    unit: str = ""  # verbatim PX unit declaration plus selected measure categories

    @property
    def text(self) -> str:
        """The fact as one line, e.g. "Year: 2024; Sex: Total = 387758"."""
        where = "; ".join(
            f"{dimension.label}: {category.label}" for dimension, category in self.categories
        )
        return f"{where} = {format_cell(self.cell)}"


def read_numbers(
    data_folder: Path, entry: CatalogueEntry, metadata: TableMetadata, selection: Selection
) -> list[Fact]:
    """The number for every combination of the selected categories, in table order."""
    choices = [
        [(dimension, dimension.category(code)) for code in selection[dimension.code]]
        for dimension in metadata.dimensions
    ]
    combinations = list(itertools.product(*choices))
    data = PxFile(data_folder / entry.folder / "data.px", metadata)
    try:
        cells = data.read_many(
            [{d.code: c.code for d, c in combination} for combination in combinations]
        )
    except KeyError as e:  # the description lists a category the data file lacks
        raise PxError(
            f"table {entry.table_code} ({entry.language}): {e.args[0]}, although the "
            "table's description lists it (Statistics Iceland's description and data "
            "disagree here)"
        ) from None
    # Reuse the existing PX parser without changing its grammar or data behavior.
    header, _ = _read_header(data_folder / entry.folder / "data.px")
    statements = _parse_statements(header)
    raw_unit = " / ".join(
        _items(statements.get(f"UNITS[{entry.language}]", statements.get("UNITS", "")))
    )
    from gagnvist.answering.category_guard import is_measure

    return [
        Fact(
            combination,
            cell,
            raw_unit + "".join(f"; {d.code}={c.label}" for d, c in combination if is_measure(d)),
        )
        for combination, cell in zip(combinations, cells, strict=True)
    ]


def format_cell(cell: Cell) -> str:
    """A number written plainly, without thousands separators, so that it reads the same
    in English and Icelandic; or what the table writes instead of a missing number."""
    if cell.value is None:
        meaning = MARKERS.get(cell.marker or "", "no value")
        return f'no number published ("{cell.marker}": {meaning})'
    if cell.value.is_integer() and abs(cell.value) < 1e15:
        return str(int(cell.value))
    return repr(cell.value)
