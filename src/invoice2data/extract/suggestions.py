"""Guided heuristics that turn candidates into first-guess fields (AUTH-2).

Given the typed candidates from :mod:`candidates`, propose a first draft of field
assignments using deterministic rules -- the same "collect all values of a type,
then pick by min/max/position" idea used by OCA's ``account_invoice_import_simple_pdf``:

* of the captured dates, the **earliest** is most likely the invoice ``date`` and
  the **latest** the ``date_due``;
* the **largest** monetary amount is most likely the total ``amount``;
* the first validated ``iban`` / ``vat`` / ``bic`` is offered as-is.

These are *suggestions* for the authoring layers (the CLI builder and AI template
generation) to present for confirmation -- never authoritative extraction.
"""

from .candidates import Candidate
from .candidates import find_candidates


def suggest_fields(candidates: list[Candidate]) -> dict[str, Candidate]:
    """Propose first-guess field assignments from typed candidates.

    Field keys use the canonical invoice vocabulary (``date``, ``date_due``,
    ``amount``, ``iban``, ``vat``, ``bic``).

    Args:
        candidates (list[Candidate]): Typed candidates from
            :func:`candidates.find_candidates`.

    Returns:
        dict[str, Candidate]: Canonical field name -> the chosen candidate. Only
            fields with a confident guess are included.
    """
    suggestions: dict[str, Candidate] = {}

    dates = sorted((c for c in candidates if c.kind == "date"), key=lambda c: c.parsed)
    if dates:
        suggestions["date"] = dates[0]  # earliest -> invoice date
        if len(dates) > 1:
            suggestions["date_due"] = dates[-1]  # latest -> due date

    amounts = sorted(
        (c for c in candidates if c.kind == "amount"),
        key=lambda c: c.parsed,
        reverse=True,
    )
    if amounts:
        suggestions["amount"] = amounts[0]  # largest -> total

    for kind in ("iban", "vat", "bic"):
        match = next((c for c in candidates if c.kind == kind), None)
        if match is not None:
            suggestions[kind] = match

    return suggestions


def suggest_from_text(text: str) -> dict[str, Candidate]:
    """Extract candidates from text and return first-guess field assignments.

    Convenience wrapper around :func:`candidates.find_candidates` +
    :func:`suggest_fields` for the authoring layers.

    Args:
        text (str): The document's extracted text.

    Returns:
        dict[str, Candidate]: Canonical field name -> the chosen candidate.
    """
    return suggest_fields(find_candidates(text))
