"""Apply tax-summary rates onto invoice lines by code (issue #535)."""

from invoice2data.extract.invoice_template import _apply_tax_to_lines


def test_apply_tax_to_lines_by_code() -> None:
    output = {
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
    output = {
        "lines": [
            {"name": "X", "price_subtotal": 100.0, "line_tax_code": "1",
             "line_tax_percent": 6.0},
        ],
        "tax_lines": [{"line_tax_code": "1", "line_tax_percent": 9.0}],
    }
    _apply_tax_to_lines(output)
    assert output["lines"][0]["line_tax_percent"] == 6.0  # explicit value kept


def test_apply_tax_to_lines_noop_without_codes() -> None:
    output = {
        "lines": [{"name": "X", "price_subtotal": 100.0}],
        "tax_lines": [{"line_tax_percent": 21.0, "price_subtotal": 100.0}],
    }
    _apply_tax_to_lines(output)
    assert "line_tax_percent" not in output["lines"][0]
