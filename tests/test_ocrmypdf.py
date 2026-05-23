import sys
import types
from pathlib import Path

import pytest

from invoice2data.input import ocrmypdf


def test_to_text_returns_empty_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ocrmypdf, "ocrmypdf_available", lambda: False)
    assert ocrmypdf.to_text("/nonexistent.pdf") == ""


def test_pre_process_pdf_returns_none_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ocrmypdf, "ocrmypdf_available", lambda: False)
    assert ocrmypdf.pre_process_pdf("/nonexistent.pdf") is None


def test_recommended_scan_options() -> None:
    assert ocrmypdf.RECOMMENDED_SCAN_OPTIONS == {
        "deskew": True,
        "clean": True,
        "rotate_pages": True,
    }


def test_pre_process_pdf_passes_options_and_returns_cleaned_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def fake_ocr(path: str, **kwargs: object) -> int:
        captured.update(kwargs)
        Path(str(kwargs["output_file"])).write_bytes(b"%PDF-1.4 cleaned")
        return 0

    fake_module = types.SimpleNamespace(ocr=fake_ocr)
    monkeypatch.setitem(sys.modules, "ocrmypdf", fake_module)
    monkeypatch.setattr(ocrmypdf, "ocrmypdf_available", lambda: True)

    src = tmp_path / "invoice.pdf"
    src.write_bytes(b"%PDF-1.4")

    out = ocrmypdf.pre_process_pdf(str(src), pre_conf={"deskew": True})

    assert out is not None
    assert Path(out).exists()  # cleaned PDF returned for the caller to save
    assert captured["deskew"] is True  # pre-processing knob forwarded
    assert captured["redo_ocr"] is True  # default preserved
    assert "invoice2data_ocrmypdf_" in out  # unique temp dir, collision-safe
