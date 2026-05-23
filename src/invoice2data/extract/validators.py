"""Lightweight, offline validators for disambiguating extracted identifiers.

Field-type regexes overlap -- an IBAN and an EU VAT number can match each other's
pattern -- so a captured value is classified by *validating* it rather than by the
regex alone: try the strong checksum first (IBAN mod-97), then the format checks
(VAT, BIC). Pure-Python, no network, no heavy deps.

Used by the template-authoring suggestion layer (to assign a captured value to the
right canonical field) and as an optional soft-validation of extracted fields. For
full per-country VAT/IBAN checksum coverage, ``python-stdnum`` can be layered on
later; this module stays dependency-free.
"""

import re


# EU VAT number formats (full, including the country prefix). Greece uses "EL".
# Extend as needed -- this is a format check, not a per-country checksum.
_VAT_PATTERNS = {
    "AT": r"ATU\d{8}",
    "BE": r"BE[01]\d{9}",
    "BG": r"BG\d{9,10}",
    "CY": r"CY\d{8}[A-Z]",
    "CZ": r"CZ\d{8,10}",
    "DE": r"DE\d{9}",
    "DK": r"DK\d{8}",
    "EE": r"EE\d{9}",
    "EL": r"EL\d{9}",
    "ES": r"ES[A-Z0-9]\d{7}[A-Z0-9]",
    "FI": r"FI\d{8}",
    "FR": r"FR[A-Z0-9]{2}\d{9}",
    "HR": r"HR\d{11}",
    "HU": r"HU\d{8}",
    "IE": r"IE(?:\d{7}[A-Z]{1,2}|\d[A-Z]\d{5}[A-Z])",
    "IT": r"IT\d{11}",
    "LT": r"LT(?:\d{9}|\d{12})",
    "LU": r"LU\d{8}",
    "LV": r"LV\d{11}",
    "MT": r"MT\d{8}",
    "NL": r"NL\d{9}B\d{2}",
    "PL": r"PL\d{10}",
    "PT": r"PT\d{9}",
    "RO": r"RO\d{2,10}",
    "SE": r"SE\d{12}",
    "SI": r"SI\d{8}",
    "SK": r"SK\d{10}",
}
_VAT_RE = re.compile("|".join(f"(?:{pattern})" for pattern in _VAT_PATTERNS.values()))
_IBAN_RE = re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}")
_BIC_RE = re.compile(r"[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?")


def _normalize(value: str) -> str:
    """Strip whitespace and upper-case a candidate identifier.

    Args:
        value (str): Raw captured value.

    Returns:
        str: Whitespace-free, upper-cased value.
    """
    return re.sub(r"\s+", "", value).upper()


def validate_iban(value: str) -> bool:
    """Return whether value is a structurally valid IBAN (ISO 13616 mod-97).

    Args:
        value (str): Candidate IBAN; spaces and case are ignored.

    Returns:
        bool: True if the structure and the mod-97 checksum are both valid.
    """
    iban = _normalize(value)
    if not _IBAN_RE.fullmatch(iban):
        return False
    # Move the first four characters to the end, then map letters to numbers
    # (A=10 .. Z=35) and check the remainder mod 97 equals 1.
    rearranged = iban[4:] + iban[:4]
    digits = "".join(str(int(char, 36)) for char in rearranged)
    return int(digits) % 97 == 1


def validate_vat(value: str) -> bool:
    """Return whether value matches a known EU VAT number format.

    Args:
        value (str): Candidate VAT number; spaces and case are ignored.

    Returns:
        bool: True if it matches a supported country's VAT format. This is a
            format check, not a per-country checksum.
    """
    return bool(_VAT_RE.fullmatch(_normalize(value)))


def validate_bic(value: str) -> bool:
    """Return whether value matches the SWIFT/BIC format (ISO 9362).

    Args:
        value (str): Candidate BIC; spaces and case are ignored.

    Returns:
        bool: True if it is a structurally valid 8- or 11-character BIC.
    """
    return bool(_BIC_RE.fullmatch(_normalize(value)))


#: Validators in discriminating order -- strongest (checksum) first, so an IBAN is
#: never mistaken for a VAT number.
VALIDATORS = {
    "iban": validate_iban,
    "vat": validate_vat,
    "bic": validate_bic,
}


def classify_identifier(value: str) -> str | None:
    """Classify a captured value as one of the known identifier types.

    Runs the validators in discriminating order (IBAN mod-97 checksum first, then
    the format-based VAT/BIC checks) so overlapping patterns resolve correctly --
    e.g. a value that passes the IBAN checksum is reported as ``"iban"`` even
    though it may also look VAT-shaped.

    Args:
        value (str): The captured string to classify.

    Returns:
        str | None: The matching key ("iban", "vat" or "bic"), or None if nothing
            validates.
    """
    for key, validator in VALIDATORS.items():
        if validator(value):
            return key
    return None
