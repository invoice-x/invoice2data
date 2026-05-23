"""Tests for the canonical field schema + validation (A3)."""

from invoice2data.extract import schema


def test_canonical_fields_pass() -> None:
    output = {
        "amount": 1.0,
        "invoice_number": "X",
        "vat": "Y",
        "currency": "EUR",
    }
    assert schema.validate_output(output) == []


def test_custom_field_is_quiet() -> None:
    # a legitimate custom field, not close to any canonical name -> no suggestion
    assert schema.validate_output({"booking_id": "X"}) == [("booking_id", None)]


def test_typo_gets_suggestion() -> None:
    assert schema.validate_output({"ammount": 1.0}) == [("ammount", "amount")]


def test_auto_typed_prefixes_recognized() -> None:
    assert schema.validate_output({"amount_total": 1.0, "date_shipped": "x"}) == []


def test_extra_fields_whitelist() -> None:
    assert schema.validate_output({"booking_id": "X"}, extra_fields=["booking_id"]) == []


def test_line_and_tax_line_fields_validated() -> None:
    output = {
        "lines": [{"name": "x", "qty": 1.0, "weird_field": 1}],
        "tax_lines": [{"line_tax_percent": 21.0, "line_tax_amount": 1.0}],
    }
    issues = schema.validate_output(output)
    assert ("weird_field", None) in issues
