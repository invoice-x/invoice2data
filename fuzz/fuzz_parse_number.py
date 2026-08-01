"""OSS-Fuzz harness for `InvoiceTemplate.parse_number`.

Locale-dependent number parsing is a classic crash surface. The library
contract: the parser returns a float, or raises a ValueError-subclass typed
error. Any other exception class is a real bug.
"""

import sys

import atheris


with atheris.instrument_imports():
    from invoice2data.exceptions import InvoiceProcessingError
    from invoice2data.extract.invoice_template import InvoiceTemplate


_TEMPLATE = InvoiceTemplate(
    {
        "template_name": "fuzz.yml",
        "keywords": ["Anything"],
        "exclude_keywords": [],
        "options": {
            "currency": "EUR",
            "decimal_separator": ".",
            "date_formats": [],
            "languages": ["en"],
            "replace": [],
        },
    }
)


def TestOneInput(data: bytes) -> None:  # noqa: N802 (Atheris harness convention)
    """Fuzz entry point. See module docstring for the contract."""
    fdp = atheris.FuzzedDataProvider(data)
    # Cap the input size so the fuzzer spends time on shape variety, not size.
    value = fdp.ConsumeUnicodeNoSurrogates(64)
    try:
        _TEMPLATE.parse_number(value)
    except (ValueError, InvoiceProcessingError):
        return  # documented failure mode


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
