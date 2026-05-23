"""Canonical output-field vocabulary and (opt-in) validation.

The field names below mirror ``docs/recommended-template-fields.md`` and the
OCA ``account_invoice_import_invoice2data`` Odoo module. This is the single
source of truth used by validation (and, later, the benchmark quality scoring).

Validation is intentionally conservative: templates may legitimately emit custom
fields, so :func:`validate_output` only flags an unrecognized field when it looks
like a *typo* of a canonical name. A template can opt into strict checking and
whitelist custom fields via its ``options`` (``strict_fields`` / ``extra_fields``).
"""

from collections.abc import Iterable
from difflib import get_close_matches
from typing import Any


#: Canonical top-level (invoice-level) field names.
INVOICE_FIELDS: frozenset[str] = frozenset(
    {
        # partner / issuer
        "issuer",
        "vat",
        "partner_name",
        "partner_street",
        "partner_street2",
        "partner_street3",
        "partner_city",
        "partner_zip",
        "country_code",
        "state_code",
        "partner_email",
        "partner_website",
        "telephone",
        "mobile",
        "partner_ref",
        "siren",
        "partner_coc",
        "company_vat",
        # document
        "amount",
        "amount_untaxed",
        "amount_tax",
        "date",
        "date_due",
        "date_start",
        "date_end",
        "invoice_number",
        "currency",
        "currency_symbol",
        "bic",
        "iban",
        "note",
        "narration",
        "payment_reference",
        "payment_unece_code",
        "incoterm",
        "mandate_id",
        # arrays + auto-added
        "lines",
        "tax_lines",
        "desc",
    }
)

#: Canonical per-line-item field names.
LINE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "product",
        "taxes",
        "code",
        "barcode",
        "qty",
        "unece_code",
        "uom",
        "price_unit",
        "price_subtotal",
        "price_total",
        "discount",
        "line_tax_percent",
        "line_tax_amount",
        "line_note",
        "sectionheader",
        "date_start",
        "date_end",
    }
)

#: Canonical per-rate tax-line field names.
TAX_LINE_FIELDS: frozenset[str] = frozenset(
    {
        "price_subtotal",
        "line_tax_percent",
        "line_tax_amount",
        "line_tax_code",
    }
)

#: Non-canonical line/tax-line field names mapped to their canonical equivalent.
#: Applied to the *output* (not the templates) by :func:`normalize_line_fields`,
#: so a template may keep these aliases and still produce the standard vocabulary.
#: ``product`` is intentionally absent — it is a distinct field (product
#: matching), not a synonym for ``name``. ``description`` maps to ``name``
#: because Odoo reads a line's label from ``name`` (``description`` is only an
#: invoice-level field for single-line imports).
LINE_FIELD_ALIASES: dict[str, str] = {
    "description": "name",
    "unit_price": "price_unit",
    "unitprice": "price_unit",
    "vat_rate": "line_tax_percent",
    "tax_percent": "line_tax_percent",
}


def normalize_line_fields(output: dict[str, Any]) -> None:
    """Rename non-canonical keys in ``lines``/``tax_lines`` rows in place.

    Maps each alias in :data:`LINE_FIELD_ALIASES` to its canonical name so that
    extraction output uses one vocabulary regardless of the group names a
    template happens to use. An alias is only applied when the canonical key is
    not already present (so an explicit canonical value always wins).

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
            for alias, canonical in LINE_FIELD_ALIASES.items():
                if alias in row and canonical not in row:
                    row[canonical] = row.pop(alias)


# Prefixes that auto-type a field (a name starting with these is intentional,
# e.g. amount_total, date_shipped), so they are never treated as unknown.
_AUTO_PREFIXES = ("amount", "date")


def _is_recognized(name: str, known: frozenset[str], extra: frozenset[str]) -> bool:
    return name in known or name in extra or name.startswith(_AUTO_PREFIXES)


def _check(
    names: Iterable[str], known: frozenset[str], extra: frozenset[str]
) -> list[tuple[str, str | None]]:
    issues: list[tuple[str, str | None]] = []
    for name in names:
        if _is_recognized(name, known, extra):
            continue
        match = get_close_matches(name, known, n=1, cutoff=0.88)
        issues.append((name, match[0] if match else None))
    return issues


def validate_output(
    output: dict[str, Any], extra_fields: Iterable[str] = ()
) -> list[tuple[str, str | None]]:
    """Find unrecognized field names in an extracted output.

    Checks top-level fields against :data:`INVOICE_FIELDS`, ``lines`` items
    against :data:`LINE_FIELDS`, and ``tax_lines`` items against
    :data:`TAX_LINE_FIELDS`. Recognized names, auto-typed (``amount*``/``date*``)
    names, and names in ``extra_fields`` are ignored.

    Args:
        output (dict[str, Any]): The extracted-fields dictionary.
        extra_fields (Iterable[str]): Custom field names to treat as known.

    Returns:
        list[tuple[str, str | None]]: ``(field_name, suggestion)`` pairs for each
            unrecognized field; ``suggestion`` is the closest canonical name if
            the field looks like a typo, else None.
    """
    extra = frozenset(extra_fields)
    issues = _check(output.keys(), INVOICE_FIELDS, extra)
    for item in output.get("lines", []) or []:
        if isinstance(item, dict):
            issues += _check(item.keys(), LINE_FIELDS, extra)
    for item in output.get("tax_lines", []) or []:
        if isinstance(item, dict):
            issues += _check(item.keys(), TAX_LINE_FIELDS, extra)
    return issues
