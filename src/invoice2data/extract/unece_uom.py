"""UNECE Recommendation 20 unit-of-measure normalization.

Templates capture a ``uom`` literal exactly as printed on the invoice (e.g.
``"l"``, ``"PS"``, ``"kg"``), but downstream tooling — and especially the OCA
Odoo importer — wants a canonical code (UNECE Rec 20: ``"LTR"`` for litre,
``"H87"`` for piece, ``"KGM"`` for kilogram, ...).

This module bridges the gap:

- :data:`UNECE_CODES` -- a small lookup mapping common literals (case- and
  whitespace-insensitive) to their UNECE Rec 20 code.
- :func:`normalize_uom` -- ``str | None`` lookup for a single literal.
- :func:`normalize_lines_uom` -- mutates an extraction's ``lines`` rows,
  filling in ``unece_code`` from ``uom`` when missing. Never overwrites an
  explicit ``unece_code``; unknown literals are left alone and logged at debug.

Soft normalization by design: the convention is recommended for *submitted*
templates, but a downstream consumer can still see the printed literal in
``uom`` and the canonical code in ``unece_code``.

References:
    UNECE Rec 20 (Codes for Units of Measure used in International Trade):
    https://unece.org/trade/uncefact/cl-recommendations
"""

from logging import getLogger
from typing import Any


__all__ = ["UNECE_CODES", "normalize_lines_uom", "normalize_uom"]

logger = getLogger(__name__)


#: Literal-to-UNECE-code lookup. Keys are pre-lower-cased; lookup strips
#: whitespace + lower-cases the input. Add entries here when a new template
#: surfaces a printed UoM the codebase doesn't recognise; aim for the published
#: UNECE Rec 20 codes (the OCA Odoo importer uses these verbatim).
UNECE_CODES: dict[str, str] = {
    # litre
    "l": "LTR",
    "ltr": "LTR",
    "lt": "LTR",
    "ℓ": "LTR",  # noqa: RUF001 — Greek script-small-L is the intended printed litre symbol
    "liter": "LTR",
    "litre": "LTR",
    "liters": "LTR",
    "litres": "LTR",
    # millilitre
    "ml": "MLT",
    "millilitre": "MLT",
    "milliliter": "MLT",
    # kilogram
    "kg": "KGM",
    "kgm": "KGM",
    "kgs": "KGM",
    "kilogram": "KGM",
    "kilograms": "KGM",
    # gram
    "g": "GRM",
    "gr": "GRM",
    "grm": "GRM",
    "gram": "GRM",
    "grams": "GRM",
    # metre / centimetre / millimetre / kilometre
    "m": "MTR",
    "mtr": "MTR",
    "meter": "MTR",
    "metre": "MTR",
    "meters": "MTR",
    "metres": "MTR",
    "cm": "CMT",
    "mm": "MMT",
    "km": "KMT",
    # piece (H87 = "piece" in invoicing; what most printed UoMs labelled
    # "pcs"/"st"/"unit"/etc actually mean):
    "pcs": "H87",
    "pc": "H87",
    "piece": "H87",
    "pieces": "H87",
    "ea": "H87",
    "each": "H87",
    "ps": "H87",
    "st": "H87",
    "stk": "H87",
    "stuk": "H87",
    "stuks": "H87",
    "stück": "H87",
    "stueck": "H87",
    "stueckliste": "H87",
    "unit": "H87",
    "units": "H87",
    "stk.": "H87",
    "x": "H87",
    # set
    "set": "SET",
    "sets": "SET",
    # hour / minute / day / month / year
    "h": "HUR",
    "hr": "HUR",
    "hrs": "HUR",
    "hour": "HUR",
    "hours": "HUR",
    "uur": "HUR",
    "uren": "HUR",
    "min": "MIN",
    "minute": "MIN",
    "minutes": "MIN",
    "d": "DAY",
    "day": "DAY",
    "days": "DAY",
    "dag": "DAY",
    "dagen": "DAY",
    "month": "MON",
    "months": "MON",
    "maand": "MON",
    "maanden": "MON",
    "mnd": "MON",
    "year": "ANN",
    "years": "ANN",
    "jaar": "ANN",
}


def normalize_uom(value: str | None) -> str | None:
    """Return the UNECE Rec 20 code for a printed UoM literal.

    Match is case- and whitespace-insensitive. Returns ``None`` for unknown
    literals and for empty/``None`` input (so callers can chain it as
    ``code = normalize_uom(line.get("uom"))`` without a guard).

    Args:
        value (str | None): The printed UoM (e.g. ``"l"``, ``"PS"``).

    Returns:
        str | None: The UNECE Rec 20 code, or ``None`` if not recognised.
    """
    if not value:
        return None
    return UNECE_CODES.get(value.strip().lower())


def normalize_lines_uom(output: dict[str, Any]) -> None:
    """Auto-populate ``unece_code`` from ``uom`` on each line, in place.

    Walks ``output["lines"]`` and ``output["tax_lines"]`` (when present) and,
    for each row that has a ``uom`` but no ``unece_code``, fills in
    ``unece_code`` from the lookup. Existing ``unece_code`` values are never
    overwritten -- a template that already captures the canonical code wins.

    Args:
        output (dict[str, Any]): The extracted-fields dictionary, mutated in
            place.
    """
    for array_field in ("lines", "tax_lines"):
        rows = output.get(array_field)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            if row.get("unece_code"):
                continue
            code = normalize_uom(row.get("uom"))
            if code:
                row["unece_code"] = code
            elif row.get("uom"):
                logger.debug(
                    "uom %r has no known UNECE code; leaving unece_code unset",
                    row["uom"],
                )
