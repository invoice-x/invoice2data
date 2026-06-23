"""Build a JSON Schema for invoice extraction from the canonical field registry.

The canonical vocabulary in :mod:`invoice2data.extract.schema` is the single
source of truth; this turns it into a JSON Schema so an LLM's structured-output
mode can be constrained to the exact fields invoice2data understands.
"""

from typing import Any

from ..extract.schema import INVOICE_FIELDS
from ..extract.schema import LINE_FIELDS


_NUMERIC_HINTS = (
    "amount",
    "price",
    "quantity",
    "qty",
    "percent",
    "subtotal",
    "total",
    "tax_amount",
)


def _field_schema(name: str) -> dict[str, str]:
    """Return the JSON-Schema type for a canonical field name.

    Args:
        name (str): Canonical field name.

    Returns:
        dict[str, str]: ``{"type": "number"}`` for monetary/quantity fields,
            otherwise ``{"type": "string"}`` (dates are ISO strings).
    """
    if any(hint in name for hint in _NUMERIC_HINTS):
        return {"type": "number"}
    return {"type": "string"}


def invoice_json_schema() -> dict[str, Any]:
    """Return a JSON Schema describing the canonical invoice output.

    Top-level invoice fields plus a ``lines`` array of line items, typed from the
    canonical registries.

    Returns:
        dict[str, Any]: A JSON Schema object suitable for structured-output APIs.
    """
    properties: dict[str, Any] = {
        name: _field_schema(name) for name in sorted(INVOICE_FIELDS)
    }
    line_properties = {name: _field_schema(name) for name in sorted(LINE_FIELDS)}
    properties["lines"] = {
        "type": "array",
        "items": {"type": "object", "properties": line_properties},
    }
    return {"type": "object", "properties": properties}
