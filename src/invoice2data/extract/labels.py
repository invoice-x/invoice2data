r"""Label-driven field detection for the template builder.

Invoices are full of predictable ``label [separator] value`` pairs --
``BTW: NL123456B01``, ``KVK. 12345678``, ``Invoice No: 2024-001``. The label does
two useful things:

* it **disambiguates** the value -- a Chamber-of-Commerce number is just digits,
  so only the ``KVK`` / ``CoC`` label tells you what it is; and
* it gives a robust **regex anchor** (``BTW\\s*:?\\s*(...)`` beats a bare value
  pattern).

This complements :mod:`candidates`, which finds typed values by pattern
regardless of label. Here we go the other way: look for known labels (with
multilingual synonyms) and capture the value next to them. Used by the
deterministic template builder to draft fields and guide the user.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LabelSpec:
    """A canonical field, the labels that introduce it, and its value pattern.

    Attributes:
        field (str): Canonical invoice field the label maps to.
        labels (tuple[str, ...]): Label synonyms (any language) that introduce it.
        value (str): Regex (no group) matching the value that follows the label.
    """

    field: str
    labels: tuple[str, ...]
    value: str
    cleanup: tuple[tuple[str, str], ...] = ()


# Identifier value shapes. Country-prefixed VAT vs. digit-only CoC is what makes
# the label essential to tell them apart. The patterns deliberately *capture the
# noisy form* (dots inside a VAT id, a place name next to a CoC number) so a
# ``cleanup`` replace can normalise it -- the template stays robust on the next
# invoice even if this sample happens to be clean.
_VAT = r"[A-Z]{2}[A-Z0-9][A-Z0-9.\-]{5,18}"  # e.g. NL12.34.56.789.B01
_COC = (
    r"(?=[A-Za-z0-9.\- ]*\d{4})[A-Za-z0-9][A-Za-z0-9.\- ]{5,27}"  # 12345678 Amsterdam
)
# Require a digit so a generic label like "Invoice" can't capture a plain word
# (e.g. the "Date" in "Invoice Date").
_DOCNO = r"(?=[A-Za-z0-9.\-/]*\d)[A-Za-z0-9][A-Za-z0-9.\-/]{2,20}"
_IBAN = r"[A-Z]{2}\d{2}[A-Z0-9 ]{10,30}"
_BIC = r"[A-Z0-9]{8,11}"
_DATE = r"\d[\d /.\-]{6,12}\d"
_AMOUNT = r"[\d., ]{2,15}\d"

#: Ordered so more specific fields claim their span first (e.g. ``Due Date``
#: before ``Date``); the first match per field wins and claimed spans are not
#: reused.
LABEL_SPECS: tuple[LabelSpec, ...] = (
    LabelSpec("iban", ("IBAN",), _IBAN),
    LabelSpec("bic", ("BIC/SWIFT", "SWIFT/BIC", "SWIFT", "BIC"), _BIC),
    LabelSpec(
        "vat",
        (
            "VAT identification number",
            "VAT Number",
            "VAT No",
            "VAT ID",
            "VAT",
            "BTW-nummer",
            "BTW nummer",
            "BTW-nr",
            "BTW nr",
            "BTW",
            "TVA",
            "USt-IdNr",
            "USt-Id",
            "USt",
            "IVA",
            "Tax ID",
            "Tax Number",
        ),
        _VAT,
        # Drop separators people sprinkle in (NL12.34.56.789.B01 -> NL123456789B01).
        cleanup=(("[^A-Z0-9]", ""),),
    ),
    LabelSpec(
        "partner_coc",
        (
            "Chamber of Commerce",
            "Company Registration",
            "Company Number",
            "Company No",
            "Registration No",
            "Reg No",
            "KvK-nummer",
            "KvK nummer",
            "KvK-nr",
            "KvK",
            "KVK",
            "CoC",
            "Handelsregister",
            "HRB",
            "SIRET",
            "SIREN",
        ),
        _COC,
        # Keep just the digits; drop the place a NL CoC line often appends
        # (e.g. "12345678 Amsterdam" -> "12345678").
        cleanup=((r"\D", ""),),
    ),
    LabelSpec(
        "invoice_number",
        (
            "Invoice Number",
            "Invoice No",
            "Invoice #",
            "Invoice",
            "Factuurnummer",
            "Factuurnr",
            "Factuur",
            "Rechnungsnummer",
            "Rechnung Nr",
            "Facture",
            "Bill No",
        ),
        _DOCNO,
    ),
    LabelSpec(
        "date_due",
        (
            "Due Date",
            "Payment Due",
            "Date Due",
            "Vervaldatum",
            "Vervaldag",
            "Echeance",
            "Fälligkeitsdatum",
            "Fälligkeit",
        ),
        _DATE,
    ),
    LabelSpec(
        "date",
        (
            "Invoice Date",
            "Factuurdatum",
            "Rechnungsdatum",
            "Date d'émission",
            "Datum",
            "Date",
        ),
        _DATE,
    ),
    LabelSpec(
        "amount",
        (
            "Total Due",
            "Amount Due",
            "Grand Total",
            "Total Amount",
            "Total",
            "Totaal",
            "Te betalen",
            "Gesamtbetrag",
            "Montant total",
        ),
        _AMOUNT,
    ),
)


@dataclass(frozen=True)
class LabeledMatch:
    """A value found next to a known label.

    Attributes:
        field (str): Canonical field the label maps to.
        label (str): The label exactly as it appears in the document.
        value (str): The captured value.
        start (int): Start offset of the value in the source text.
        end (int): End offset of the value in the source text.
        value_pattern (str): The value regex (for building the field's template
            regex).
        cleanup (tuple[tuple[str, str], ...]): ``(pattern, replacement)`` pairs to
            sanitise the captured value (becomes the field's ``replace``).
    """

    field: str
    label: str
    value: str
    start: int
    end: int
    value_pattern: str
    cleanup: tuple[tuple[str, str], ...] = ()


def _compile(spec: LabelSpec) -> re.Pattern[str]:
    """Build a ``label[sep](value)`` matcher for a spec (label case-insensitive).

    Args:
        spec (LabelSpec): The field/label/value spec.

    Returns:
        re.Pattern[str]: Compiled pattern; group 1 is the label, group 2 the value.
    """
    # Longest labels first so "Invoice Number" wins over "Invoice".
    ordered = sorted(spec.labels, key=lambda label: len(label), reverse=True)
    alt = "|".join(re.escape(label) for label in ordered)
    # Case-insensitive label only (scoped flag); value stays case-sensitive so a
    # country-prefixed VAT id isn't matched as lowercase noise.
    sep = r"[ \t]*[:.#=\-]?[ \t]*"
    return re.compile(rf"((?i:{alt})){sep}({spec.value})")


def find_labeled_fields(text: str) -> dict[str, LabeledMatch]:
    """Find ``label: value`` pairs for known fields in document text.

    The first match per field wins; spans already claimed by an earlier (more
    specific) field are not reused, so e.g. ``Due Date`` is claimed by ``date_due``
    and a later plain ``Date`` match over the same text is skipped.

    Args:
        text (str): The document's extracted text.

    Returns:
        dict[str, LabeledMatch]: Canonical field name -> the labeled match.
    """
    results: dict[str, LabeledMatch] = {}
    claimed: list[tuple[int, int]] = []
    for spec in LABEL_SPECS:
        for match in _compile(spec).finditer(text):
            span = (match.start(), match.end())
            if any(start < span[1] and span[0] < end for start, end in claimed):
                continue
            results[spec.field] = LabeledMatch(
                field=spec.field,
                label=match.group(1),
                value=match.group(2).strip(),
                start=match.start(2),
                end=match.end(2),
                value_pattern=spec.value,
                cleanup=spec.cleanup,
            )
            claimed.append(span)
            break
    return results
