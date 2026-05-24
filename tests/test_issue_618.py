"""The used template name is included in the output (issue #618)."""

from pathlib import Path

from invoice2data import extract_data
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import prepare_template


def test_output_includes_template_name(tmp_path: Path) -> None:
    template = InvoiceTemplate(
        prepare_template(
            {
                "template_name": "my.test.yml",
                "issuer": "Test Issuer",
                "keywords": ["INVOICE"],
                "fields": {
                    "date": r"Date:\s*(\d{4}-\d{2}-\d{2})",
                    "amount": r"Total:\s*(\d+\.\d+)",
                    "invoice_number": r"No:\s*(\S+)",
                },
            }
        )
    )
    sample = tmp_path / "doc.txt"
    sample.write_text(
        "INVOICE\nDate: 2024-05-07\nTotal: 10.00\nNo: A-1\n", encoding="utf-8"
    )

    result = extract_data(str(sample), templates=[template])

    assert result["template_name"] == "my.test.yml"
    assert result["issuer"] == "Test Issuer"
