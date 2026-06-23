"""Apply tax-summary rates onto invoice lines by code (issue #535)."""

from typing import Any

from invoice2data.extract.invoice_template import _apply_tax_to_lines
from invoice2data.extract.invoice_template import _single_active_rate


def test_apply_tax_to_lines_by_code() -> None:
    output: dict[str, Any] = {
        "lines": [
            {"name": "Diesel", "price_subtotal": 100.0, "line_tax_code": "2"},
            {"name": "Coffee", "price_subtotal": 10.0, "line_tax_code": "1"},
            {"name": "NoCode", "price_subtotal": 5.0},
        ],
        "tax_lines": [
            {"line_tax_code": "1", "line_tax_percent": 9.0},
            {"line_tax_code": "2", "line_tax_percent": 21.0},
        ],
    }
    _apply_tax_to_lines(output)

    assert output["lines"][0]["line_tax_percent"] == 21.0
    assert output["lines"][0]["line_tax_amount"] == 21.0  # 100 * 21%
    assert output["lines"][1]["line_tax_percent"] == 9.0
    assert output["lines"][1]["line_tax_amount"] == 0.9  # 10 * 9%
    assert "line_tax_percent" not in output["lines"][2]  # no code -> untouched


def test_apply_tax_to_lines_does_not_overwrite() -> None:
    output: dict[str, Any] = {
        "lines": [
            {
                "name": "X",
                "price_subtotal": 100.0,
                "line_tax_code": "1",
                "line_tax_percent": 6.0,
            },
        ],
        "tax_lines": [{"line_tax_code": "1", "line_tax_percent": 9.0}],
    }
    _apply_tax_to_lines(output)
    assert output["lines"][0]["line_tax_percent"] == 6.0  # explicit value kept


def test_apply_tax_to_lines_ignores_non_list_inputs() -> None:
    # Missing or wrong-typed tax_lines/lines -> no error, no change.
    out1: dict[str, Any] = {"lines": [{"name": "X"}]}  # no tax_lines key
    _apply_tax_to_lines(out1)
    assert "line_tax_percent" not in out1["lines"][0]

    out2: dict[str, Any] = {"tax_lines": "nope", "lines": [{"name": "X"}]}
    _apply_tax_to_lines(out2)
    assert "line_tax_percent" not in out2["lines"][0]


def test_single_active_rate_skips_non_dict_rows() -> None:
    rows = ["junk", {"line_tax_percent": 21.0, "price_subtotal": 5.0}]
    assert _single_active_rate(rows) == 21.0


def test_single_active_rate_picks_the_only_taxed_rate() -> None:
    # Valk-style summary: only the 21% row carries amounts -> single active rate.
    tax_lines = [
        {"line_tax_percent": 0.0, "price_subtotal": 0.0, "line_tax_amount": 0.0},
        {"line_tax_percent": 9.0, "price_subtotal": 0.0, "line_tax_amount": 0.0},
        {"line_tax_percent": 21.0, "price_subtotal": 42.73, "line_tax_amount": 8.97},
    ]
    assert _single_active_rate(tax_lines) == 21.0


def test_single_active_rate_none_when_mixed() -> None:
    tax_lines = [
        {"line_tax_percent": 9.0, "price_subtotal": 10.0, "line_tax_amount": 0.9},
        {"line_tax_percent": 21.0, "price_subtotal": 42.73, "line_tax_amount": 8.97},
    ]
    assert _single_active_rate(tax_lines) is None


def test_single_active_rate_none_when_no_amounts() -> None:
    tax_lines = [
        {"line_tax_percent": 9.0, "price_subtotal": 0.0, "line_tax_amount": 0.0},
        {"line_tax_percent": 21.0, "price_subtotal": 0.0, "line_tax_amount": 0.0},
    ]
    assert _single_active_rate(tax_lines) is None


def test_apply_single_rate_to_codeless_lines() -> None:
    # No codes anywhere, summary has one active rate -> apply it to every line.
    output: dict[str, Any] = {
        "lines": [
            {"name": "Room", "price_subtotal": 30.0},
            {"name": "Breakfast", "price_subtotal": 12.73},
        ],
        "tax_lines": [
            {"line_tax_percent": 9.0, "price_subtotal": 0.0, "line_tax_amount": 0.0},
            {
                "line_tax_percent": 21.0,
                "price_subtotal": 42.73,
                "line_tax_amount": 8.97,
            },
        ],
    }
    _apply_tax_to_lines(output)
    assert output["lines"][0]["line_tax_percent"] == 21.0
    assert output["lines"][0]["line_tax_amount"] == 6.3  # 30 * 21%
    assert output["lines"][1]["line_tax_percent"] == 21.0


def test_no_single_rate_applied_when_mixed() -> None:
    output: dict[str, Any] = {
        "lines": [{"name": "X", "price_subtotal": 100.0}],
        "tax_lines": [
            {"line_tax_percent": 9.0, "price_subtotal": 10.0, "line_tax_amount": 0.9},
            {"line_tax_percent": 21.0, "price_subtotal": 90.0, "line_tax_amount": 18.9},
        ],
    }
    _apply_tax_to_lines(output)
    assert "line_tax_percent" not in output["lines"][0]  # ambiguous -> untouched


def test_apply_tax_to_lines_noop_without_codes_single_rate_still_applies() -> None:
    # A single non-zero rate now DOES enrich code-less lines (case 1, issue #535).
    output: dict[str, Any] = {
        "lines": [{"name": "X", "price_subtotal": 100.0}],
        "tax_lines": [{"line_tax_percent": 21.0, "price_subtotal": 100.0}],
    }
    _apply_tax_to_lines(output)
    assert output["lines"][0]["line_tax_percent"] == 21.0
    assert output["lines"][0]["line_tax_amount"] == 21.0
