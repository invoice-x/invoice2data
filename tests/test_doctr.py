import sys
import types
from typing import Any

import pytest

from invoice2data.input import doctr


def test_to_text_returns_empty_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(doctr, "doctr_available", lambda: False)
    assert doctr.to_text("/nonexistent.pdf") == ""


def _install_fake_doctr(
    monkeypatch: pytest.MonkeyPatch, result: Any, calls: dict[str, str]
) -> None:
    """Inject fake doctr / doctr.io / doctr.models modules into sys.modules."""

    def from_pdf(path: str) -> list[str]:
        calls["pdf"] = path
        return ["pdf-doc"]

    def from_images(path: str) -> list[str]:
        calls["img"] = path
        return ["img-doc"]

    fake_io = types.ModuleType("doctr.io")
    fake_io.DocumentFile = types.SimpleNamespace(  # type: ignore[attr-defined]
        from_pdf=from_pdf, from_images=from_images
    )
    fake_models = types.ModuleType("doctr.models")
    fake_models.ocr_predictor = lambda pretrained=True: (  # type: ignore[attr-defined]
        lambda doc: result
    )
    monkeypatch.setitem(sys.modules, "doctr", types.ModuleType("doctr"))
    monkeypatch.setitem(sys.modules, "doctr.io", fake_io)
    monkeypatch.setitem(sys.modules, "doctr.models", fake_models)
    doctr._get_model.cache_clear()


def test_to_text_uses_render_and_pdf_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, str] = {}

    class FakeResult:
        def render(self) -> str:
            return "ACME Corp\nTotal 121.00"

    _install_fake_doctr(monkeypatch, FakeResult(), calls)
    try:
        text = doctr.to_text("sample.PDF")
    finally:
        doctr._get_model.cache_clear()

    assert "ACME Corp" in text
    assert "121.00" in text
    assert calls["pdf"] == "sample.PDF"  # .pdf -> from_pdf


def test_to_text_image_loader_and_export_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, str] = {}

    class ExportOnlyResult:  # no render() -> exercises the export fallback
        def export(self) -> dict[str, Any]:
            return {
                "pages": [
                    {
                        "blocks": [
                            {
                                "lines": [
                                    {"words": [{"value": "Hello"}, {"value": "World"}]}
                                ]
                            }
                        ]
                    }
                ]
            }

    _install_fake_doctr(monkeypatch, ExportOnlyResult(), calls)
    try:
        text = doctr.to_text("scan.png")
    finally:
        doctr._get_model.cache_clear()

    assert text == "Hello World"
    assert calls["img"] == "scan.png"  # non-pdf -> from_images
