"""Label-driven field detection for the template builder."""

import re

from invoice2data.extract.labels import find_labeled_fields
from invoice2data.extract.template_builder import _labeled_regex
from invoice2data.extract.template_builder import preview_field
from invoice2data.extract.template_builder import suggested_template


SAMPLE = """ACME B.V.
Invoice No: 2024-00123
Invoice Date: 2024-05-12
Due Date: 2024-06-11
BTW: NL123456789B01
KVK: 12345678
IBAN: NL91 ABNA 0417 1643 00
BIC: ABNANL2A
Total Due: 1.234,56
"""


def test_detects_labeled_fields() -> None:
    found = find_labeled_fields(SAMPLE)
    assert found["invoice_number"].value == "2024-00123"
    assert found["date"].value == "2024-05-12"
    assert found["date_due"].value == "2024-06-11"
    assert found["vat"].value == "NL123456789B01"
    assert found["partner_coc"].value == "12345678"  # digits-only: needs the KVK label
    assert found["bic"].value == "ABNANL2A"
    assert found["iban"].value.startswith("NL91 ABNA")


def test_multilingual_label_maps_to_canonical_field() -> None:
    found = find_labeled_fields("TVA FR12345678901\nChamber of Commerce 99887766")
    assert found["vat"].value == "FR12345678901"  # TVA -> vat
    assert found["partner_coc"].value == "99887766"  # CoC synonym -> partner_coc


def test_due_date_not_confused_with_date() -> None:
    found = find_labeled_fields("Due Date: 2024-06-11\nDate: 2024-05-12")
    assert found["date_due"].value == "2024-06-11"
    assert found["date"].value == "2024-05-12"


def test_generated_regex_round_trips() -> None:
    # Every label-anchored regex must actually capture its value from the source.
    for match in find_labeled_fields(SAMPLE).values():
        pattern = _labeled_regex(match)
        m = re.search(pattern, SAMPLE)
        assert m is not None, pattern
        assert m.group(1).strip() == match.value


def test_builder_includes_label_only_fields() -> None:
    template = suggested_template(SAMPLE)
    # partner_coc + invoice_number are identifiable only via their labels.
    assert "partner_coc" in template["fields"]
    assert "invoice_number" in template["fields"]
    # The drafted field captures (and cleans) the value.
    assert preview_field(template["fields"]["partner_coc"], SAMPLE) == "12345678"


def test_vat_cleanup_strips_separators() -> None:
    template = suggested_template("ACME\nBTW: NL12.34.56.789.B01\n")
    spec = template["fields"]["vat"]
    assert isinstance(spec, dict)  # cleanup -> field dict with replace
    assert preview_field(spec, "BTW: NL12.34.56.789.B01") == "NL123456789B01"


def test_coc_cleanup_keeps_only_digits() -> None:
    template = suggested_template("ACME\nKvK: 12345678 Amsterdam\n")
    assert preview_field(
        template["fields"]["partner_coc"], "KvK 12345678 Amsterdam"
    ) == ("12345678")
