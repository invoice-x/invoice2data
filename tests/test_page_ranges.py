"""Template-wide page ranges apply before keyword matching and extraction."""

import types
from logging import DEBUG
from pathlib import Path
from typing import Any

import pytest

from invoice2data.api import _match_template_for_reader
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import prepare_template


def _page_reader() -> types.ModuleType:
    """Return a backend whose text makes its selected range observable."""
    module = types.ModuleType("page_reader")
    module.SUPPORTS_PAGES = True  # type: ignore[attr-defined]
    module.SUPPORTS_AREA = True  # type: ignore[attr-defined]

    def to_text(
        _path: str,
        area_details: dict[str, Any] | None = None,
        pages: tuple[int, int] | None = None,
    ) -> str:
        _ = area_details
        return f"page {pages[0]}-{pages[1]}" if pages else "all pages"

    module.to_text = to_text  # type: ignore[attr-defined]
    return module


def test_scoped_template_matches_only_its_selected_pages(tmp_path: Path) -> None:
    """Page scoping is applied before a template's keywords are evaluated."""
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    template = InvoiceTemplate(
        {
            "template_name": "page-two.yml",
            "keywords": ["page 2-3"],
            "exclude_keywords": [],
            "pages": "2-3",
        }
    )

    selected, selected_text = _match_template_for_reader(
        "all pages", [template], str(pdf), _page_reader()
    )

    assert selected is template
    assert selected_text == "page 2-3"


@pytest.mark.parametrize(
    "value, expected", [(2, (2, 2)), ("2", (2, 2)), ("2-3", (2, 3))]
)
def test_page_syntax_is_accepted(value: Any, expected: tuple[int, int]) -> None:
    from invoice2data.input import parse_pages

    assert parse_pages(value) == expected


@pytest.mark.parametrize("value", ["0", "2-", "3-2", "two", [2, 3]])
def test_invalid_page_syntax_is_rejected(value: Any) -> None:
    from invoice2data.input import parse_pages

    with pytest.raises((TypeError, ValueError), match="pages must"):
        parse_pages(value)


def test_area_is_limited_to_the_template_page_range(tmp_path: Path) -> None:
    """A field area cannot escape a template-wide page restriction."""
    from invoice2data.input import extract_text

    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    calls: list[tuple[dict[str, Any] | None, tuple[int, int] | None]] = []
    reader = _page_reader()

    def to_text(
        _path: str,
        area_details: dict[str, Any] | None = None,
        pages: tuple[int, int] | None = None,
    ) -> str:
        calls.append((area_details, pages))
        return "area"

    reader.to_text = to_text  # type: ignore[attr-defined]
    assert extract_text(reader, str(pdf), {"f": 1, "l": 3}, pages="2-3") == "area"
    assert calls == [({"f": 2, "l": 3}, (2, 3))]
    assert extract_text(reader, str(pdf), {"f": 1, "l": 1}, pages="2-3") == ""


def test_template_area_receives_the_template_page_range(tmp_path: Path) -> None:
    """The template passes its page scope through to a field area."""
    from invoice2data.extract.invoice_template import _handle_area

    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    reader = _page_reader()
    template = InvoiceTemplate(
        {
            "template_name": "page-two.yml",
            "keywords": ["page 2-3"],
            "exclude_keywords": [],
            "pages": "2-3",
        }
    )

    assert (
        _handle_area(
            template,
            {"area": {"f": 1, "l": 3}},
            reader,
            str(pdf),
            "all pages",
            template["pages"],
        )
        == "page 2-3"
    )


def test_page_scoped_template_skips_unsupported_reader(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Cascade matching skips, rather than warns for, an unsuitable reader."""
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    reader = _page_reader()
    reader.SUPPORTS_PAGES = False  # type: ignore[attr-defined]
    template = InvoiceTemplate(
        {
            "template_name": "page-two.yml",
            "keywords": ["page 2-3"],
            "exclude_keywords": [],
            "pages": "2-3",
        }
    )
    caplog.set_level(DEBUG)

    selected, _text = _match_template_for_reader(
        "all pages", [template], str(pdf), reader
    )

    assert selected is None
    assert "cannot use pages" in caplog.text


def test_selector_scoped_pages_can_match_and_extract_different_pages(
    tmp_path: Path,
) -> None:
    """Matching, scalar fields and modern lines each own their page scope."""
    pdf = tmp_path / "envelope-and-invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    reader = _page_reader()

    def to_text(
        _path: str,
        area_details: dict[str, Any] | None = None,
        pages: tuple[int, int] | None = None,
    ) -> str:
        _ = area_details
        content = {
            None: "ENVELOPE SUPPLIER REF: G1\nINVOICE: INV-42\nLINE Widget",
            (1, 1): "ENVELOPE SUPPLIER REF: G1",
            (2, 3): "INVOICE: INV-42\nLINES START\nLINE Widget\nLINES END",
        }
        return content[pages]

    reader.to_text = to_text  # type: ignore[attr-defined]
    prepared = prepare_template(
        {
            "template_name": "supplier.yml",
            "match": {"pages": 1, "keywords": ["ENVELOPE", "SUPPLIER"]},
            "required_fields": [],
            "fields": {
                "invoice_number": {
                    "parser": "regex",
                    "pages": "2-3",
                    "regex": r"INVOICE: (\S+)",
                },
                "payment_reference": {
                    "parser": "regex",
                    "pages": 1,
                    "regex": r"REF: (\S+)",
                },
                "lines": {
                    "parser": "lines",
                    "pages": "2-3",
                    "start": "LINES START",
                    "end": "LINES END",
                    "line": r"LINE (?P<name>\w+)",
                },
            },
        }
    )
    assert prepared is not None
    template = InvoiceTemplate(prepared)

    selected, document_text = _match_template_for_reader(
        to_text(str(pdf)), [template], str(pdf), reader
    )

    assert selected is template
    assert document_text.startswith("ENVELOPE")
    result = template.extract(document_text, str(pdf), reader)
    assert result["invoice_number"] == "INV-42"
    assert result["payment_reference"] == "G1"
    assert result["lines"] == [{"name": "Widget"}]


def test_match_selector_rejects_ambiguous_legacy_keywords() -> None:
    """A template chooses either the explicit match selector or legacy keys."""
    assert (
        prepare_template(
            {
                "template_name": "ambiguous.yml",
                "keywords": "legacy",
                "pages": 1,
                "match": {"keywords": "modern"},
            }
        )
        is None
    )
