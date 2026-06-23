"""extract_data(raise_on_error=True) raises typed exceptions (#190)."""

from pathlib import Path

import pytest

from invoice2data import extract_data
from invoice2data.exceptions import InvoiceProcessingError
from invoice2data.exceptions import NoTemplateFoundError
from invoice2data.exceptions import RequiredFieldsMissingError
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import read_templates
from invoice2data.input import text


TEMPLATE = (
    "issuer: ACME\n"
    "keywords:\n  - ACME\n"
    "required_fields:\n  - invoice_number\n"
    "fields:\n"
    "  amount:\n"
    "    parser: regex\n"
    "    regex: 'Total (\\d+\\.\\d+)'\n"
    "    type: float\n"
)


def _setup(tmp_path: Path, body: str) -> tuple[list[InvoiceTemplate], str]:
    tdir = tmp_path / "templates"
    tdir.mkdir()
    (tdir / "acme.yml").write_text(TEMPLATE, encoding="utf-8")
    invoice = tmp_path / "inv.txt"
    invoice.write_text(body, encoding="utf-8")
    return read_templates(str(tdir)), str(invoice)


def test_returns_empty_by_default(tmp_path: Path) -> None:
    templates, invoice = _setup(tmp_path, "nothing matches here\n")
    assert extract_data(invoice, templates=templates, input_module=text) == {}


def test_no_template_found_raises(tmp_path: Path) -> None:
    templates, invoice = _setup(tmp_path, "nothing matches here\n")
    with pytest.raises(NoTemplateFoundError):
        extract_data(
            invoice, templates=templates, input_module=text, raise_on_error=True
        )


def test_required_fields_missing_raises(tmp_path: Path) -> None:
    # Keyword matches, but the required invoice_number is never captured.
    templates, invoice = _setup(tmp_path, "ACME Corp\nTotal 100.00\n")
    with pytest.raises(RequiredFieldsMissingError) as excinfo:
        extract_data(
            invoice, templates=templates, input_module=text, raise_on_error=True
        )
    assert "invoice_number" in excinfo.value.fields


def test_exception_hierarchy() -> None:
    err = RequiredFieldsMissingError({"invoice_number"}, "acme.yml")
    assert isinstance(err, InvoiceProcessingError)
    assert isinstance(err, ValueError)  # keeps the cascade's except ValueError working
    assert "invoice_number" in str(err)
    assert err.template_name == "acme.yml"
