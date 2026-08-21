"""Template-wide page ranges apply before keyword matching and extraction."""

import types
from pathlib import Path

import pytest

from invoice2data.api import _match_template_for_reader
from invoice2data.extract.invoice_template import InvoiceTemplate


def _page_reader() -> types.ModuleType:
    """Return a backend whose text makes its selected range observable."""
    module = types.ModuleType("page_reader")
    module.SUPPORTS_PAGES = True  # type: ignore[attr-defined]

    def to_text(_path: str, _area=None, pages=None) -> str:
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


@pytest.mark.parametrize("value, expected", [(2, (2, 2)), ("2", (2, 2)), ("2-3", (2, 3))])
def test_page_syntax_is_accepted(value, expected) -> None:
    from invoice2data.input import parse_pages

    assert parse_pages(value) == expected


@pytest.mark.parametrize("value", ["0", "3-2", "two", [2, 3]])
def test_invalid_page_syntax_is_rejected(value) -> None:
    from invoice2data.input import parse_pages

    with pytest.raises((TypeError, ValueError), match="pages must"):
        parse_pages(value)
