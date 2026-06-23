"""Tiered, cached date parsing.

Order, fastest applicable first:

1. the template's explicit ``date_formats`` via stdlib ``datetime.strptime``
   (microseconds, deterministic);
2. ``dateutil`` (fast, fuzzy, English-centric);
3. ``dateparser`` (slow, but multilingual / localized month names) -- which is an
   **optional** dependency (``pip install invoice2data[dateparser]``).

With dateparser absent, localized month-name dates won't parse, but numeric and
English dates still do via tiers 1-2. Results are memoized (absolute-date parsing
is deterministic for given inputs).
"""

import contextlib
import datetime
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=8)
def _date_data_parser(languages: tuple[str, ...]) -> Any:
    """Return a reused dateparser ``DateDataParser``, or None if it's not installed.

    Args:
        languages (tuple[str, ...]): Language codes, or empty for auto-detect.

    Returns:
        Any: A ``DateDataParser``, or None when dateparser is unavailable.
    """
    try:
        from dateparser.date import DateDataParser
    except ImportError:
        return None
    return DateDataParser(languages=list(languages) or None)


def _try_strptime(
    value: str, date_formats: tuple[str, ...]
) -> datetime.datetime | None:
    """Parse with the template's explicit formats via ``strptime``.

    Args:
        value (str): The date string.
        date_formats (tuple[str, ...]): Candidate ``strptime`` formats.

    Returns:
        datetime.datetime | None: The parsed datetime, or None if none matched.
    """
    for fmt in date_formats:
        with contextlib.suppress(ValueError, TypeError):
            return datetime.datetime.strptime(value, fmt)
    return None


def _try_dateutil(value: str) -> datetime.datetime | None:
    """Parse with ``dateutil`` (fuzzy, English-centric).

    Args:
        value (str): The date string.

    Returns:
        datetime.datetime | None: The parsed datetime, or None on failure.
    """
    from dateutil import parser as dateutil_parser

    try:
        parsed: datetime.datetime = dateutil_parser.parse(value)
    except (ValueError, OverflowError, TypeError):
        return None
    return parsed


def _try_dateparser(
    value: str, date_formats: tuple[str, ...], languages: tuple[str, ...]
) -> datetime.datetime | None:
    """Parse with the optional ``dateparser`` (multilingual/localized).

    Args:
        value (str): The date string.
        date_formats (tuple[str, ...]): Candidate formats, or empty for any.
        languages (tuple[str, ...]): Language codes, or empty for auto-detect.

    Returns:
        datetime.datetime | None: The parsed datetime, or None (incl. when
            dateparser is not installed).
    """
    parser = _date_data_parser(languages)
    if parser is None:
        return None
    date_obj: datetime.datetime | None = parser.get_date_data(
        value, date_formats=list(date_formats) or None
    ).date_obj
    return date_obj


@lru_cache(maxsize=4096)
def parse_date(
    value: str,
    date_formats: tuple[str, ...] = (),
    languages: tuple[str, ...] = (),
) -> datetime.datetime | None:
    """Parse a date string using the tiered strategy (memoized).

    Args:
        value (str): The date string to parse.
        date_formats (tuple[str, ...]): Template formats, tried first via strptime.
        languages (tuple[str, ...]): Language codes for the dateparser fallback.

    Returns:
        datetime.datetime | None: The parsed datetime, or None.
    """
    if not value:
        return None
    cleaned = value.strip()
    result = _try_strptime(cleaned, date_formats)
    if result is not None:
        return result
    result = _try_dateutil(cleaned)
    if result is not None:
        return result
    return _try_dateparser(value, date_formats, languages)
