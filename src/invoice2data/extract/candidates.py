"""Candidate extraction for guided / AI-assisted template authoring (AUTH-1).

Scans a document's extracted text for typed candidate values -- dates, monetary
amounts and identifiers (IBAN/VAT/BIC) -- each with its position in the text. The
template-authoring layers (the copier-style CLI builder and AI template
generation) consume these candidates to propose fields/regexes; the guided
heuristics (AUTH-2) turn them into first-guess field assignments.

Pure-Python: reuses the offline :mod:`validators` to type identifiers and
``dateparser`` (already a dependency) to parse dates.
"""

import datetime
import re
from dataclasses import dataclass
from typing import Any

import dateparser  # type: ignore[import-untyped]

from .validators import classify_identifier


@dataclass(frozen=True)
class Candidate:
    """A typed value found in document text.

    Attributes:
        kind (str): Candidate type -- "date", "amount", "iban", "vat" or "bic".
        value (str): The raw substring as it appears in the text.
        start (int): Start character offset in the source text.
        end (int): End character offset in the source text.
        parsed (Any): Normalised value -- a ``datetime`` for dates, a ``float`` for
            amounts, the whitespace-stripped identifier for iban/vat/bic.
    """

    kind: str
    value: str
    start: int
    end: int
    parsed: Any


_DATE_RE = re.compile(
    r"\b\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4}\b"  # 2024-05-12, 12/05/2024
    r"|\b\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{2,4}\b"  # 12 May 2024
    r"|\b[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{2,4}\b"  # May 12, 2024
)
_AMOUNT_RE = re.compile(
    r"(?<![\d.,])\d{1,3}(?:[.,\s]\d{3})+[.,]\d{2}(?!\d)"  # grouped: 1.234,56
    r"|(?<![\d.,])\d+[.,]\d{2}(?!\d)"  # plain: 1234.56 / 12,50
)
# Contiguous identifier tokens (VAT, BIC, IBAN written without spaces).
_TOKEN_RE = re.compile(r"\b[A-Z0-9]{5,40}\b")
# IBANs printed in space-separated groups of 2-4 (mandatory single spaces, so it
# never merges with a preceding label word).
_SPACED_IBAN_RE = re.compile(r"[A-Z]{2}\d{2}(?: [A-Z0-9]{2,4}){2,8}")


def _to_float(raw: str) -> float | None:
    """Parse a monetary string to a float, guessing the decimal separator.

    The separator that appears last is treated as the decimal mark; the other is
    stripped as a thousands separator.

    Args:
        raw (str): The matched amount substring.

    Returns:
        float | None: The parsed value, or None if it cannot be parsed.
    """
    value = raw.replace(" ", "")
    if value.rfind(",") > value.rfind("."):
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(",", "")
    try:
        return float(value)
    except ValueError:
        return None


def find_dates(text: str) -> list[Candidate]:
    """Find parseable date candidates in text.

    Args:
        text (str): The document's extracted text.

    Returns:
        list[Candidate]: Date candidates whose value ``dateparser`` could parse.
    """
    candidates = []
    for match in _DATE_RE.finditer(text):
        parsed = dateparser.parse(match.group())
        if isinstance(parsed, datetime.datetime):
            candidates.append(
                Candidate("date", match.group(), match.start(), match.end(), parsed)
            )
    return candidates


def find_amounts(text: str) -> list[Candidate]:
    """Find parseable monetary-amount candidates in text.

    Args:
        text (str): The document's extracted text.

    Returns:
        list[Candidate]: Amount candidates with a parsed float value.
    """
    candidates = []
    for match in _AMOUNT_RE.finditer(text):
        parsed = _to_float(match.group())
        if parsed is not None:
            candidates.append(
                Candidate("amount", match.group(), match.start(), match.end(), parsed)
            )
    return candidates


def find_identifiers(text: str) -> list[Candidate]:
    """Find validated identifier candidates (IBAN/VAT/BIC) in text.

    Each potential identifier is classified via :func:`validators.classify_identifier`
    so overlapping patterns resolve correctly (e.g. an IBAN is not mistaken for a
    VAT number).

    Args:
        text (str): The document's extracted text.

    Returns:
        list[Candidate]: Identifier candidates with ``kind`` set to the validated
            type and ``parsed`` to the whitespace-stripped value, sorted by
            position.
    """
    found: dict[tuple[int, int], Candidate] = {}
    # Pass 1: contiguous tokens (VAT, BIC, unspaced IBAN).
    for match in _TOKEN_RE.finditer(text):
        kind = classify_identifier(match.group())
        if kind is not None:
            normalized = re.sub(r"\s+", "", match.group()).upper()
            found[match.span()] = Candidate(
                kind, match.group(), match.start(), match.end(), normalized
            )
    # Pass 2: space-grouped IBANs not already covered by a contiguous token.
    for match in _SPACED_IBAN_RE.finditer(text):
        if classify_identifier(match.group()) != "iban":
            continue
        if any(start < match.end() and match.start() < end for start, end in found):
            continue
        normalized = re.sub(r"\s+", "", match.group()).upper()
        found[match.span()] = Candidate(
            "iban", match.group(), match.start(), match.end(), normalized
        )
    return sorted(found.values(), key=lambda c: c.start)


def _overlaps(candidate: Candidate, spans: list[tuple[int, int]]) -> bool:
    """Return whether a candidate's span intersects any of the given spans.

    Args:
        candidate (Candidate): The candidate to test.
        spans (list[tuple[int, int]]): (start, end) ranges to test against.

    Returns:
        bool: True if the candidate overlaps any span.
    """
    return any(
        candidate.start < span_end and span_start < candidate.end
        for span_start, span_end in spans
    )


def find_candidates(text: str) -> list[Candidate]:
    """Find all typed candidates in text, sorted by position.

    Amount candidates that fall inside a date (e.g. the ``12.05`` in
    ``12.05.2024``) are dropped to avoid double counting.

    Args:
        text (str): The document's extracted text.

    Returns:
        list[Candidate]: All date/amount/identifier candidates, ordered by
            ``start`` offset.
    """
    dates = find_dates(text)
    date_spans = [(d.start, d.end) for d in dates]
    amounts = [a for a in find_amounts(text) if not _overlaps(a, date_spans)]
    identifiers = find_identifiers(text)
    return sorted(dates + amounts + identifiers, key=lambda c: c.start)
