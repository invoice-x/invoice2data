import datetime

from invoice2data.extract.candidates import Candidate
from invoice2data.extract.candidates import find_amounts
from invoice2data.extract.candidates import find_candidates
from invoice2data.extract.candidates import find_dates
from invoice2data.extract.candidates import find_identifiers


def test_find_dates_parses_multiple_formats() -> None:
    text = "Invoice date: 2024-05-07\nDue: 12 June 2024"
    dates = find_dates(text)
    assert len(dates) == 2
    assert all(isinstance(d.parsed, datetime.datetime) for d in dates)
    # Earliest first when sorted by value -> the invoice date precedes the due date.
    by_time = sorted(dates, key=lambda c: c.parsed)
    assert by_time[0].parsed < by_time[1].parsed


def test_find_amounts_handles_separators() -> None:
    amounts = {c.value: c.parsed for c in find_amounts("Total 1.234,56 / Sub 99.00")}
    assert amounts["1.234,56"] == 1234.56
    assert amounts["99.00"] == 99.0


def test_find_identifiers_typed_via_validators() -> None:
    text = "IBAN NL91ABNA0417164300 VAT NL123456789B01 BIC DEUTDEFF"
    by_kind = {c.kind: c.parsed for c in find_identifiers(text)}
    assert by_kind["iban"] == "NL91ABNA0417164300"
    assert by_kind["vat"] == "NL123456789B01"
    assert by_kind["bic"] == "DEUTDEFF"


def test_find_identifiers_handles_spaced_iban() -> None:
    cands = find_identifiers("Pay to NL91 ABNA 0417 1643 00 please")
    assert any(c.kind == "iban" and c.parsed == "NL91ABNA0417164300" for c in cands)


def test_find_candidates_drops_amount_inside_date() -> None:
    # The "12.05" inside the date must not surface as a separate amount.
    cands = find_candidates("Date 12.05.2024 amount due 50.00")
    kinds = [c.kind for c in cands]
    assert "date" in kinds
    amounts = [c for c in cands if c.kind == "amount"]
    assert len(amounts) == 1
    assert amounts[0].parsed == 50.0


def test_find_candidates_sorted_by_position() -> None:
    cands = find_candidates("Total 10.00 on 2024-01-02 ref DEUTDEFF")
    assert cands == sorted(cands, key=lambda c: c.start)
    assert all(isinstance(c, Candidate) for c in cands)
