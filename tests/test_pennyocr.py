"""Tests for the PennyOCR input backend (network mocked)."""

import io
import json

import pytest

from invoice2data.input import INPUT_MODULES
from invoice2data.input import pennyocr


def test_registered():
    assert INPUT_MODULES["pennyocr"] is pennyocr


def test_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("PENNYOCR_API_KEY", raising=False)
    assert pennyocr.is_available() is False


def test_available_with_key(monkeypatch):
    monkeypatch.setenv("PENNYOCR_API_KEY", "pk_live_test")
    assert pennyocr.is_available() is True


def test_to_text_posts_multipart_and_returns_text(monkeypatch, tmp_path):
    monkeypatch.setenv("PENNYOCR_API_KEY", "pk_live_test")
    doc = tmp_path / "invoice.pdf"
    doc.write_bytes(b"%PDF-fake")
    captured = {}

    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["auth"] = req.get_header("Authorization")
        captured["body"] = req.data
        return FakeResponse(json.dumps({"pages": 1, "text": "TOTAL 12.34"}).encode())

    monkeypatch.setattr(pennyocr._request, "urlopen", fake_urlopen)
    text = pennyocr.to_text(str(doc))
    assert text == "TOTAL 12.34"
    assert captured["url"].endswith("format=text")
    assert captured["auth"] == "Bearer pk_live_test"
    assert b"%PDF-fake" in captured["body"]
    assert b'filename="invoice.pdf"' in captured["body"]


def test_to_text_without_key_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("PENNYOCR_API_KEY", raising=False)
    doc = tmp_path / "invoice.pdf"
    doc.write_bytes(b"%PDF-fake")
    with pytest.raises(OSError):
        pennyocr.to_text(str(doc))
