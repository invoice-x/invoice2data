"""Tiered date parsing: strptime -> dateutil -> (optional) dateparser."""

import datetime

import pytest

from invoice2data.extract import _dates
from invoice2data.extract._dates import parse_date


def test_strptime_tier_uses_template_format() -> None:
    parse_date.cache_clear()
    assert parse_date("31/12/2017", ("%d/%m/%Y",)) == datetime.datetime(2017, 12, 31)


def test_dateutil_tier_parses_iso_without_a_format() -> None:
    parse_date.cache_clear()
    assert parse_date("2017-12-31") == datetime.datetime(2017, 12, 31)


def test_dateparser_tier_handles_localized_month() -> None:
    pytest.importorskip("dateparser")
    parse_date.cache_clear()
    result = parse_date("15 mai 2024", (), ("fr",))  # French month name
    assert result is not None
    assert (result.year, result.month, result.day) == (2024, 5, 15)


def test_dateparser_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate dateparser not being installed.
    monkeypatch.setattr(_dates, "_date_data_parser", lambda languages: None)
    parse_date.cache_clear()

    # Localized month can't be parsed by strptime/dateutil -> None without dateparser.
    assert parse_date("15 mai 2024", (), ("fr",)) is None
    # Numeric / ISO dates still parse via the first two tiers.
    assert parse_date("31/12/2017", ("%d/%m/%Y",)) == datetime.datetime(2017, 12, 31)
    assert parse_date("2017-12-31") == datetime.datetime(2017, 12, 31)
    parse_date.cache_clear()
