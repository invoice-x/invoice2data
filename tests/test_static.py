"""The static pseudo-parser (extract/parsers/static.py)."""

import logging

import pytest

from invoice2data.extract.parsers import static


def test_static_returns_configured_value() -> None:
    assert static.parse(None, "currency", {"value": "EUR"}, "") == "EUR"


def test_static_missing_value_warns_and_returns_none(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        result = static.parse(None, "currency", {}, "")
    assert result is None
    assert "doesn't have static value" in caplog.text
