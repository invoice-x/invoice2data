"""Runtime LLM fallback extraction (AI-2).

Opt-in: when no template matches (or every match is missing required fields) and
OCR doesn't help, extract fields with the configured :class:`AIProvider`,
constrained to the canonical JSON schema and validated. Results are tagged
``extraction_method: "ai"`` so they are never confused with a deterministic
template match. Off unless explicitly enabled.
"""

import contextlib
import logging
from typing import Any

import dateparser  # type: ignore[import-untyped]

from ..extract import schema
from .__interface__ import AIProvider
from .__interface__ import get_provider
from .schema_json import invoice_json_schema


logger = logging.getLogger(__name__)

_INSTRUCTIONS = (
    "You extract structured data from the text of a business document (usually an "
    "invoice). Return ONLY a JSON object matching the provided schema. Use null for "
    "any field you cannot find; never invent values."
)


def _coerce(raw: dict[str, Any]) -> dict[str, Any]:
    """Drop empty values and coerce dates/amounts to template-style types.

    Args:
        raw (dict[str, Any]): The provider's raw JSON result.

    Returns:
        dict[str, Any]: Cleaned fields (``datetime`` for ``date*``, ``float`` for
            ``amount*`` where possible).
    """
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if value in (None, "", []):
            continue
        if key.startswith("date") and isinstance(value, str):
            parsed = dateparser.parse(value)
            cleaned[key] = parsed if parsed is not None else value
        elif key.startswith("amount") and not isinstance(value, (int, float)):
            with contextlib.suppress(ValueError, TypeError):
                value = float(value)
            cleaned[key] = value
        else:
            cleaned[key] = value
    return cleaned


def ai_fallback_extract(
    text: str, *, provider: AIProvider | None = None
) -> dict[str, Any]:
    """Extract fields from text via the configured AI provider (opt-in).

    Args:
        text (str): The document's extracted text.
        provider (AIProvider | None): Provider to use; the configured one
            (:func:`get_provider`) when None.

    Returns:
        dict[str, Any]: Extracted fields tagged ``extraction_method: "ai"``, or an
            empty dict when text is empty, the provider is unavailable, or nothing
            was found.
    """
    if not text:
        return {}
    provider = provider or get_provider()
    if not provider.is_available():
        logger.warning("AI fallback requested but no provider is available.")
        return {}
    logger.info("No template matched; trying AI fallback extraction.")
    raw = provider.extract_structured(
        text, invoice_json_schema(), instructions=_INSTRUCTIONS
    )
    result = _coerce(raw)
    if not result:
        return {}
    schema.normalize_line_fields(result)
    for name, suggestion in schema.validate_output(result):
        hint = f" (did you mean {suggestion!r}?)" if suggestion else ""
        logger.warning("AI fallback produced unrecognized field %r%s", name, hint)
    result["extraction_method"] = "ai"
    return result
