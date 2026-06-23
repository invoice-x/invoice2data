"""The fast spike backends (hotpdf, pdf-oxide), with the optional dep mocked.

These exercise ``input/hotpdf.py`` and ``input/pdfoxide.py`` without installing
hotpdf / pdf-oxide, mirroring the doctr/paddleocr/camelot test approach.
"""

import sys
import types

import pytest

from invoice2data.input import INPUT_MODULES
from invoice2data.input import hotpdf
from invoice2data.input import pdfoxide


def test_backends_are_registered() -> None:
    assert INPUT_MODULES.get("hotpdf") is hotpdf
    assert INPUT_MODULES.get("pdfoxide") is pdfoxide


def test_hotpdf_is_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    assert hotpdf.is_available() is True
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    assert hotpdf.is_available() is False


def test_hotpdf_to_text_joins_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHotPdf:
        def __init__(self, path: str) -> None:
            self.pages = [object(), object()]  # two pages

        def extract_page_text(self, index: int) -> str:
            return f"page{index}"

    monkeypatch.setitem(sys.modules, "hotpdf", types.SimpleNamespace(HotPdf=FakeHotPdf))
    assert hotpdf.to_text("invoice.pdf") == "page0\npage1"


def test_pdfoxide_is_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    assert pdfoxide.is_available() is True
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    assert pdfoxide.is_available() is False


def test_pdfoxide_to_text_uses_layout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakePdfDocument:
        def __init__(self, path: str) -> None:
            captured["path"] = path

        def to_plain_text_all(self, preserve_layout: bool) -> str:
            captured["preserve_layout"] = preserve_layout
            return "oxide text"

    monkeypatch.setitem(
        sys.modules, "pdf_oxide", types.SimpleNamespace(PdfDocument=FakePdfDocument)
    )
    assert pdfoxide.to_text("invoice.pdf") == "oxide text"
    assert captured["path"] == "invoice.pdf"
    assert captured["preserve_layout"] is True  # layout mode scored best in benchmark
