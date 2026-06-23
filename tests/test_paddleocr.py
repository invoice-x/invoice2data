import sys
import types

import pytest

from invoice2data.input import paddleocr


def test_to_text_returns_empty_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(paddleocr, "paddleocr_available", lambda: False)
    assert paddleocr.to_text("/nonexistent.png") == ""


def test_extract_text_v2_format() -> None:
    result = [
        [
            [[[0, 0], [1, 0], [1, 1], [0, 1]], ("ACME Corp", 0.99)],
            [[[0, 2], [1, 2], [1, 3], [0, 3]], ("Total 121.00", 0.98)],
        ]
    ]
    assert paddleocr._extract_text(result) == "ACME Corp\nTotal 121.00"


def test_extract_text_v3_dict_format() -> None:
    result = [{"rec_texts": ["ACME Corp", "Total 121.00"]}]
    assert paddleocr._extract_text(result) == "ACME Corp\nTotal 121.00"


def test_to_text_image_via_fake_paddleocr(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeOCR:
        def __init__(self, **kwargs: object) -> None:
            captured["kwargs"] = kwargs

        def ocr(self, source: object, **kwargs: object) -> object:
            captured["source"] = source
            return [[[[[0, 0]], ("Hello", 0.9)], [[[0, 1]], ("World", 0.9)]]]

    fake_module = types.ModuleType("paddleocr")
    fake_module.PaddleOCR = FakeOCR  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)
    monkeypatch.setattr(paddleocr, "paddleocr_available", lambda: True)
    paddleocr._get_ocr.cache_clear()

    try:
        text = paddleocr.to_text("scan.png", lang="de")
    finally:
        paddleocr._get_ocr.cache_clear()

    assert text == "Hello\nWorld"
    assert captured["source"] == "scan.png"  # image path passed straight through
    assert captured["kwargs"] == {"lang": "de"}  # lang forwarded to the engine
