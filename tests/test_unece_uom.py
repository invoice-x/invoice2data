"""UNECE Rec 20 UoM normalization."""

from typing import Any

from invoice2data.extract.unece_uom import normalize_lines_uom
from invoice2data.extract.unece_uom import normalize_uom


def test_normalize_uom_known_literal() -> None:
    assert normalize_uom("l") == "LTR"
    assert normalize_uom("PCS") == "H87"
    assert normalize_uom("kg") == "KGM"


def test_normalize_uom_case_and_whitespace_insensitive() -> None:
    assert normalize_uom(" Liter ") == "LTR"
    assert normalize_uom("StUk") == "H87"


def test_normalize_uom_unknown_returns_none() -> None:
    assert normalize_uom("widgets") is None


def test_normalize_uom_empty_inputs_return_none() -> None:
    assert normalize_uom("") is None
    assert normalize_uom(None) is None


def test_normalize_lines_fills_unece_code_when_missing() -> None:
    output: dict[str, Any] = {
        "lines": [
            {"name": "Widget", "uom": "pcs", "qty": 3},
            {"name": "Fuel", "uom": "l", "qty": 12.5},
        ],
    }
    normalize_lines_uom(output)
    assert output["lines"][0]["unece_code"] == "H87"
    assert output["lines"][1]["unece_code"] == "LTR"


def test_normalize_lines_never_overwrites_existing_unece_code() -> None:
    output: dict[str, Any] = {
        "lines": [
            # Template explicitly captured unece_code; should win.
            {"name": "Widget", "uom": "pcs", "unece_code": "EA"},
        ],
    }
    normalize_lines_uom(output)
    assert output["lines"][0]["unece_code"] == "EA"


def test_normalize_lines_leaves_unknown_uom_alone() -> None:
    output: dict[str, Any] = {"lines": [{"name": "Quirky", "uom": "widgets"}]}
    normalize_lines_uom(output)
    assert "unece_code" not in output["lines"][0]
    assert output["lines"][0]["uom"] == "widgets"  # not mutated


def test_normalize_lines_handles_missing_lines_key() -> None:
    output: dict[str, Any] = {}
    normalize_lines_uom(output)
    assert output == {}


def test_normalize_lines_handles_non_list_lines() -> None:
    # Some templates produce a single-line `lines` value as a dict — should be
    # ignored rather than crash.
    output: dict[str, Any] = {"lines": {"not": "a list"}}
    normalize_lines_uom(output)
    assert output == {"lines": {"not": "a list"}}


def test_normalize_lines_also_walks_tax_lines() -> None:
    output: dict[str, Any] = {"tax_lines": [{"uom": "kg"}]}
    normalize_lines_uom(output)
    assert output["tax_lines"][0]["unece_code"] == "KGM"


def test_normalize_lines_skips_non_dict_rows() -> None:
    # Mixed list (a row is somehow a string) — should not crash.
    output: dict[str, Any] = {"lines": ["bogus", {"uom": "l"}]}
    normalize_lines_uom(output)
    assert output["lines"][1]["unece_code"] == "LTR"
