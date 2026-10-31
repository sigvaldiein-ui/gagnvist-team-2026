"""Synthetic evidence checks, independent of the open/closed evaluation answers."""

from dataclasses import replace

import pytest

from gagnvist.answering.category_guard import guard_totals
from gagnvist.answering.choose_categories import Choice
from gagnvist.answering.grounded_answer import cell_references, render_plan
from gagnvist.answering.read_numbers import Fact
from gagnvist.answering.write_answer import unsupported_numbers
from gagnvist.data.catalogue import CatalogueEntry, Category, Dimension, TableMetadata
from gagnvist.data.px_reader import Cell

YEAR = Dimension("Year", "Year", (Category("2017", "2017"), Category("2018", "2018")), True)
SEX = Dimension(
    "Sex", "Sex", (Category("T", "Total"), Category("F", "Females"), Category("M", "Males")), False
)
ENTRY = CatalogueEntry(
    "demo/en/test/T1",
    "en",
    "T1",
    "Synthetic population",
    "demo",
    "https://example.test/table",
    "2018-01-01",
    6,
    None,
)


def fact(year: str, sex: str, value: float | None, unit: str = "persons") -> Fact:
    return Fact(((YEAR, YEAR.category(year)), (SEX, SEX.category(sex))), Cell(value, None), unit)


def plan(op: str, ids: list[str], roles: list[str], mode: str) -> dict:
    return {
        "outputs": [
            {"operation": op, "cell_references": ids, "operand_roles": roles, "period_mode": mode}
        ]
    }


def test_guard_corrects_only_unique_unspecified_total() -> None:
    choice = Choice({"Year": ["2017"], "Sex": ["F"]}, [])
    result = guard_totals(
        "Population?",
        TableMetadata("t", (YEAR, SEX)),
        choice,
        {"Year": "unspecified", "Sex": "unspecified"},
    )
    assert result.selection == {"Year": ["2017"], "Sex": ["T"]}
    assert choice.selection["Sex"] == ["F"]


@pytest.mark.parametrize("scope", [None, {}, {"Sex": "explicit"}, {"Sex": "uncertain"}])
def test_guard_abstains_without_explicit_unspecified_scope(scope: object) -> None:
    choice = Choice({"Sex": ["F"]}, [])
    assert guard_totals("Population?", TableMetadata("t", (SEX,)), choice, scope) == choice


@pytest.mark.parametrize(
    "label,question",
    [
        ("Females", "How many females?"),
        ("Males", "How many males?"),
        ("18-25 years", "People aged 18-25?"),
        ("Akureyri", "Íbúar á Akureyri?"),
    ],
)
def test_explicit_category_vetoes_incorrect_model_scope(label: str, question: str) -> None:
    dim = Dimension("group", "group", (Category("t", "Total"), Category("a", label)), False)
    choice = Choice({"group": ["a"]}, [])
    result = guard_totals(question, TableMetadata("t", (dim,)), choice, {"group": "unspecified"})
    assert result.selection == choice.selection


@pytest.mark.parametrize("totals", [(), (Category("t", "Total"), Category("t2", "Alls"))])
def test_no_missing_or_ambiguous_total_is_guessed(totals: tuple[Category, ...]) -> None:
    dim = Dimension("group", "group", (Category("a", "Other"), *totals), False)
    result = guard_totals(
        "Population?",
        TableMetadata("t", (dim,)),
        Choice({"group": ["a"]}, []),
        {"group": "unspecified"},
    )
    assert result.selection == {"group": ["a"]}
    assert "abstained" in result.notes[0]


def test_guard_never_replaces_metric() -> None:
    dim = Dimension("Unit", "Unit", (Category("t", "Total"), Category("p", "Percent")), False)
    choice = Choice({"Unit": ["p"]}, [])
    assert (
        guard_totals("Rate?", TableMetadata("t", (dim,)), choice, {"Unit": "unspecified"}) == choice
    )


@pytest.mark.parametrize(
    "op,roles,expected",
    [
        ("difference", ["left", "right"], "30"),
        ("percent_change", ["new", "old"], "25"),
    ],
)
def test_arithmetic_uses_fetched_values_and_preserves_provenance(
    op: str, roles: list[str], expected: str
) -> None:
    facts = [fact("2018", "T", 150), fact("2017", "T", 120)]
    result = render_plan(
        plan(op, ["cell-aa", "cell-ab"], roles, "across_periods"), "en", ENTRY, facts
    )
    calc = result.calculations[0]
    assert calc["status"] == "verified" and calc["displayed"] == expected
    assert calc["cell_references"] == ["cell-aa", "cell-ab"]
    assert calc["period_mode"] == "across_periods"
    assert result.cell_references[0]["categories"] == {"Year": "2018", "Sex": "T"}
    assert result.cell_references[0]["table_folder"] == ENTRY.folder
    assert (
        unsupported_numbers(result.text, [*(f.text for f in facts), *result.validated_numbers])
        == []
    )


@pytest.mark.parametrize("op,expected", [("share", "40"), ("ratio", "0.4")])
def test_subgroup_and_total_same_period(op: str, expected: str) -> None:
    facts = [fact("2018", "F", 60), fact("2018", "T", 150)]
    result = render_plan(
        plan(op, ["cell-aa", "cell-ab"], ["numerator", "denominator"], "single_period"),
        "is",
        ENTRY,
        facts,
    )
    assert result.calculations[0]["displayed"] == expected


@pytest.mark.parametrize(
    "failure",
    [
        "invented_number",
        "unknown_id",
        "duplicate",
        "wrong_role",
        "reversed_period",
        "wrong_mode",
        "missing",
        "nan",
        "zero",
        "unit",
        "no_unit",
        "mixed_unit",
        "cross_group",
    ],
)
def test_invalid_calculation_is_rejected_visibly(failure: str) -> None:
    facts = [fact("2018", "T", 150), fact("2017", "T", 120)]
    proposed = plan("percent_change", ["cell-aa", "cell-ab"], ["new", "old"], "across_periods")
    output = proposed["outputs"][0]
    if failure == "invented_number":
        output["value"] = 999
    elif failure == "unknown_id":
        output["cell_references"] = ["cell-aa", "invented"]
    elif failure == "duplicate":
        output["cell_references"] = ["cell-aa", "cell-aa"]
    elif failure == "wrong_role":
        output["operand_roles"] = ["old", "new"]
    elif failure == "reversed_period":
        output["cell_references"] = ["cell-ab", "cell-aa"]
    elif failure == "wrong_mode":
        output["period_mode"] = "single_period"
    elif failure in {"missing", "nan", "zero"}:
        facts[1] = replace(
            facts[1], cell=Cell({"missing": None, "nan": float("nan"), "zero": 0.0}[failure], None)
        )
    elif failure in {"unit", "no_unit"}:
        facts[1] = replace(facts[1], unit="kg" if failure == "unit" else "")
    elif failure == "mixed_unit":
        facts = [replace(f, unit="Number / %") for f in facts]
    else:
        facts[1] = fact("2017", "F", 120)
    result = render_plan(proposed, "en", ENTRY, facts)
    assert result.calculations[0]["status"] == "rejected"
    assert result.validated_numbers == []
    assert "could not be fully verified" in result.text
    assert result.notes


def test_no_plan_keeps_fetched_cells_and_reports_failure() -> None:
    result = render_plan({"outputs": []}, "is", ENTRY, [fact("2018", "T", 150)])
    assert "150" in result.text and result.notes
    assert result.calculations == []


def test_share_cannot_use_subgroup_as_denominator() -> None:
    result = render_plan(
        plan("share", ["cell-aa", "cell-ab"], ["numerator", "denominator"], "single_period"),
        "en",
        ENTRY,
        [fact("2018", "T", 150), fact("2018", "F", 60)],
    )
    assert result.calculations[0]["status"] == "rejected"


def test_references_distinguish_all_fifty_cells() -> None:
    refs = cell_references(ENTRY, [fact("2018", "T", n) for n in range(50)])
    assert len({r["id"] for r in refs}) == 50
