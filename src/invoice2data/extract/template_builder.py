"""Deterministic template drafting for the CLI builder (AUTH-3).

Turns the AUTH candidates/suggestions into a first-draft invoice2data template
(issuer + keywords + field regexes) without any AI. The CLI builder
(``invoice2data --new-template``) presents this draft for confirmation; the
AI-assisted mode swaps this for :func:`ai.template_generator.generate_template`.
"""

import re
from typing import Any

import yaml  # type: ignore[import-untyped]

from .candidates import Candidate
from .candidates import find_candidates
from .labels import LabeledMatch
from .labels import find_labeled_fields
from .suggestions import suggest_fields


#: Capture pattern per candidate kind, used to build a field's value group.
_VALUE_PATTERNS = {
    "date": r"\d[\d/.\-]+\d",
    "amount": r"[\d.,]+",
    "iban": r"[A-Z0-9 ]+",
    "vat": r"[A-Z0-9]+",
    "bic": r"[A-Z0-9]+",
}


def field_regex_from_candidate(text: str, candidate: Candidate) -> str:
    r"""Build a field regex anchored on the label preceding a candidate value.

    Uses the text before the value on its line as a literal anchor (with flexible
    whitespace) plus a typed capture group, e.g. ``Date:\s*(\d[\d/.\-]+\d)``.

    Args:
        text (str): The full document text.
        candidate (Candidate): The candidate whose value to capture.

    Returns:
        str: A regex with one capturing group around the value.
    """
    line_start = text.rfind("\n", 0, candidate.start) + 1
    prefix = text[line_start : candidate.start].strip()
    value_pattern = _VALUE_PATTERNS.get(candidate.kind, r"\S+")
    if prefix:
        return rf"{_anchor(prefix)}\s*({value_pattern})"
    return rf"({value_pattern})"


def _anchor(literal: str) -> str:
    r"""Turn a label/prefix into a whitespace-flexible literal regex anchor.

    Each non-space token is escaped and joined with ``\s+`` so the anchor still
    matches when the document re-flows the spacing. (Escaping the whole string
    first would mangle multi-word labels, since ``re.escape`` escapes spaces.)

    Args:
        literal (str): The label or line-prefix text from the document.

    Returns:
        str: A regex fragment matching the label with flexible whitespace.
    """
    return r"\s+".join(re.escape(part) for part in literal.split())


def _labeled_regex(match: LabeledMatch) -> str:
    r"""Build a field regex anchored on a known label.

    e.g. a ``BTW: NL123…`` match becomes ``BTW\s*[:.#=\-]?\s*([A-Z]{2}…)``.

    Args:
        match (LabeledMatch): The labeled value found in the document.

    Returns:
        str: A regex with one capturing group around the value.
    """
    return rf"{_anchor(match.label)}\s*[:.#=\-]?\s*({match.value_pattern})"


def _labeled_field(match: LabeledMatch) -> str | dict[str, Any]:
    """Build a template field from a labeled match.

    A plain regex string when no cleanup is needed; otherwise a field dict with a
    ``replace`` so the captured value is sanitised (dots in a VAT id, a place name
    after a CoC number) before use.

    Args:
        match (LabeledMatch): The labeled value found in the document.

    Returns:
        str | dict[str, Any]: A regex string, or a ``{parser, regex, replace}`` dict.
    """
    regex = _labeled_regex(match)
    if not match.cleanup:
        return regex
    return {
        "parser": "regex",
        "regex": regex,
        "replace": [list(pair) for pair in match.cleanup],
    }


def field_regex(spec: str | dict[str, Any]) -> str:
    """Return the regex of a field spec (a bare string or a field dict).

    Args:
        spec (str | dict[str, Any]): A template field value.

    Returns:
        str: The field's regex pattern.
    """
    return spec["regex"] if isinstance(spec, dict) else spec


def set_field_regex(spec: str | dict[str, Any], regex: str) -> str | dict[str, Any]:
    """Return ``spec`` with its regex replaced (keeping any cleanup/replace).

    Args:
        spec (str | dict[str, Any]): The existing field spec.
        regex (str): The new regex pattern.

    Returns:
        str | dict[str, Any]: The updated spec (same shape as the input).
    """
    if isinstance(spec, dict):
        return {**spec, "regex": regex}
    return regex


def preview_field(spec: str | dict[str, Any], text: str) -> str | None:
    """Return what a field spec captures from ``text``, after any cleanup.

    Args:
        spec (str | dict[str, Any]): A template field value (regex or dict).
        text (str): The sample text to match against.

    Returns:
        str | None: The captured (and ``replace``-cleaned) value, or None if the
            regex does not match.
    """
    match = re.search(field_regex(spec), text)
    if match is None:
        return None
    value = match.group(1) if match.groups() else match.group(0)
    if isinstance(spec, dict):
        for pattern, replacement in spec.get("replace", []):
            value = re.sub(pattern, replacement, value)
    return value


def _guess_issuer(text: str) -> str:
    """Guess the issuer from the first non-empty line of text.

    Args:
        text (str): The document text.

    Returns:
        str: The first non-empty trimmed line, or an empty string.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def suggested_template(text: str) -> dict[str, Any]:
    """Draft a template from a sample's deterministic candidates (no AI).

    Args:
        text (str): The sample document's extracted text.

    Returns:
        dict[str, Any]: A template dict with ``issuer``, ``keywords`` and
            ``fields`` (canonical field name -> regex).
    """
    suggestions = suggest_fields(find_candidates(text))
    fields: dict[str, Any] = {
        field: field_regex_from_candidate(text, candidate)
        for field, candidate in suggestions.items()
    }
    # Labels give a better field than a bare value pattern: they anchor the regex
    # and add cleanup (dots in a VAT id, a place after a CoC number), and they
    # identify label-only fields (partner_coc, invoice_number). Prefer them --
    # except for date/amount, where the candidate heuristics (earliest date,
    # largest amount) pick better among several values.
    keep_value_based = {"date", "amount"}
    for field, match in find_labeled_fields(text).items():
        if field in keep_value_based and field in fields:
            continue
        fields[field] = _labeled_field(match)
    issuer = _guess_issuer(text)
    return {
        "issuer": issuer,
        "keywords": [issuer] if issuer else [],
        "fields": fields,
    }


def to_yaml(template: dict[str, Any]) -> str:
    """Serialise a template dict to YAML for writing to a ``.yml`` file.

    Args:
        template (dict[str, Any]): The template to serialise.

    Returns:
        str: The YAML document.
    """
    dumped: str = yaml.safe_dump(
        template, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    return dumped
