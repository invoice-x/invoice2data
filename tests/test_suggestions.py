from invoice2data.extract.suggestions import suggest_fields
from invoice2data.extract.suggestions import suggest_from_text


def test_suggest_from_text_picks_date_extremes_and_total() -> None:
    text = (
        "Invoice date: 2024-05-07\n"
        "Due date: 2024-06-06\n"
        "Subtotal 100.00\n"
        "VAT 21.00\n"
        "Total 121.00\n"
        "IBAN NL91ABNA0417164300\n"
    )
    suggestions = suggest_from_text(text)

    assert suggestions["date"].parsed.date().isoformat() == "2024-05-07"  # earliest
    assert suggestions["date_due"].parsed.date().isoformat() == "2024-06-06"  # latest
    assert suggestions["amount"].parsed == 121.00  # largest amount -> total
    assert suggestions["iban"].parsed == "NL91ABNA0417164300"


def test_suggest_single_date_has_no_due_date() -> None:
    suggestions = suggest_from_text("Date 2024-01-15, pay 50.00")
    assert "date" in suggestions
    assert "date_due" not in suggestions


def test_suggest_fields_empty_input() -> None:
    assert suggest_fields([]) == {}
