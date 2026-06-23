"""Tests for tax-line computation (A4)."""

from invoice2data.extract.invoice_template import _compute_line_tax


def test_line_tax_amount_computed_for_tax_lines() -> None:
    output = {"tax_lines": [{"price_subtotal": 100.0, "line_tax_percent": 21.0}]}
    _compute_line_tax(output)
    assert output["tax_lines"][0]["line_tax_amount"] == 21.0


def test_existing_line_tax_amount_not_overwritten() -> None:
    output = {
        "tax_lines": [
            {"price_subtotal": 100.0, "line_tax_percent": 21.0, "line_tax_amount": 20.5}
        ]
    }
    _compute_line_tax(output)
    assert output["tax_lines"][0]["line_tax_amount"] == 20.5


def test_product_lines_are_left_untouched() -> None:
    output = {"lines": [{"price_subtotal": 100.0, "line_tax_percent": 21.0}]}
    _compute_line_tax(output)
    assert "line_tax_amount" not in output["lines"][0]
