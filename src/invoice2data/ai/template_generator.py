"""AI-assisted template generation (AI-1).

Drafts an invoice2data template from a sample document's text using the
configured :class:`AIProvider`, grounded with the deterministic candidates from
:mod:`invoice2data.extract.suggestions` so the model has concrete values to anchor
its regexes. ``preview_template`` then round-trips the draft against the same text
so the user can see what it captures before saving it.

Authoring-time only -- this never runs during normal extraction; the default path
stays deterministic templates.
"""

import re
from typing import Any

from ..extract.suggestions import suggest_from_text
from .__interface__ import AIProvider
from .__interface__ import get_provider


#: JSON Schema for the *template* the model must produce (not the invoice values).
TEMPLATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "issuer": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "exclude_keywords": {"type": "array", "items": {"type": "string"}},
        "fields": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "required": ["keywords", "fields"],
}

_INSTRUCTIONS = (
    "You write extraction templates for the invoice2data library. Given the text "
    "of a sample invoice, return a JSON object with: 'issuer' (the company name), "
    "'keywords' (1-3 short strings that uniquely identify this issuer's documents), "
    "optional 'exclude_keywords', and 'fields' mapping canonical field names "
    "(date, invoice_number, amount, amount_untaxed, amount_tax, vat, iban) to a "
    "Python regular expression with exactly ONE capturing group around the value. "
    "Base every regex on the literal text of THIS sample so it matches. Return "
    "ONLY the JSON object."
)


def _candidate_hints(text: str) -> str:
    """Summarise detected candidates as grounding hints for the model.

    Args:
        text (str): The sample document text.

    Returns:
        str: One ``field: value`` per line, or an empty string if none found.
    """
    suggestions = suggest_from_text(text)
    return "\n".join(f"{field}: {cand.value}" for field, cand in suggestions.items())


def _normalize_template(
    draft: dict[str, Any], issuer: str | None = None
) -> dict[str, Any]:
    """Coerce a model draft into a well-formed template dict.

    Args:
        draft (dict[str, Any]): The model's raw JSON output.
        issuer (str | None): Issuer override; falls back to the draft's value.

    Returns:
        dict[str, Any]: A template with list ``keywords``, dict ``fields`` and an
            ``issuer``.
    """
    keywords = draft.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]
    fields = draft.get("fields")
    if not isinstance(fields, dict):
        fields = {}
    template: dict[str, Any] = {
        "issuer": issuer or draft.get("issuer", ""),
        "keywords": list(keywords),
        "fields": fields,
    }
    if draft.get("exclude_keywords"):
        template["exclude_keywords"] = draft["exclude_keywords"]
    return template


def generate_template(
    text: str,
    *,
    provider: AIProvider | None = None,
    issuer: str | None = None,
) -> dict[str, Any]:
    """Draft an invoice2data template from a sample document's text.

    Args:
        text (str): The sample document's extracted text.
        provider (AIProvider | None): Provider to use; the configured one
            (:func:`get_provider`) when None.
        issuer (str | None): Optional issuer name to force into the template.

    Returns:
        dict[str, Any]: A template dict (issuer/keywords/fields) ready to review,
            preview and save.
    """
    provider = provider or get_provider()
    hints = _candidate_hints(text)
    content = f"{text}\n\n# Detected values (hints):\n{hints}" if hints else text
    draft = provider.extract_structured(
        content, TEMPLATE_SCHEMA, instructions=_INSTRUCTIONS
    )
    return _normalize_template(draft, issuer=issuer)


def preview_template(template: dict[str, Any], text: str) -> dict[str, str]:
    """Apply a template's field regexes to text to preview what it captures.

    A lightweight round-trip so the user can confirm the draft before saving it;
    the real engine applies these regexes with the template's options at runtime.

    Args:
        template (dict[str, Any]): A template dict with a ``fields`` mapping of
            field name -> regex string.
        text (str): The sample text to match against.

    Returns:
        dict[str, str]: Field name -> the first captured value (group 1 when the
            regex has a group, otherwise the whole match). Fields that do not
            match are omitted.
    """
    preview: dict[str, str] = {}
    for field, spec in template.get("fields", {}).items():
        regex = spec["regex"] if isinstance(spec, dict) else spec
        if not isinstance(regex, str):
            continue
        match = re.search(regex, text)
        if match is None:
            continue
        value = match.group(1) if match.groups() else match.group(0)
        if isinstance(spec, dict):
            for pair in spec.get("replace", []):
                value = re.sub(pair[0], pair[1], value)
        preview[field] = value
    return preview
