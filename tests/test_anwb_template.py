"""Regression tests for the bundled ANWB template."""

from copy import deepcopy

import pytest

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import read_templates


pytestmark = pytest.mark.windows_strict


@pytest.mark.parametrize(
    "iban",
    [
        "NL00TEST0000000000",
        "NL00 TEST 0000 0000 00",
        "NL00-TEST-0000-0000-00",
    ],
)
@pytest.mark.parametrize("following_text", ["\n", "\nFooter text\n", "\r\nFooter text\r\n"])
def test_anwb_extracts_complete_iban(iban: str, following_text: str) -> None:
    loaded = next(t for t in read_templates() if t["template_name"] == "nl.anwb.yml")
    template = InvoiceTemplate(deepcopy(dict(loaded)))
    template["required_fields"] = ["iban"]
    text = template.prepare_input(f"Invoice\nIBAN: {iban}{following_text}")

    with pytest.warns(DeprecationWarning, match="The 'lines' plugin"):
        result = template.extract(text, "synthetic.txt", None)

    assert result["iban"] == iban
