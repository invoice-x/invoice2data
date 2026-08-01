"""OSS-Fuzz harness for `InvoiceTemplate.parse_date`.

`parse_date` walks a fastest-first cascade (stdlib `strptime` -> `dateutil`
-> optional `dateparser`) with locale-dependent format strings. It must
return a datetime, a date, or `None` -- never propagate an unexpected
exception class.
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


def TestOneInput(data: bytes) -> None:  # noqa: N802
    fdp = atheris.FuzzedDataProvider(data)
    value = fdp.ConsumeUnicodeNoSurrogates(96)
    try:
        result = _TEMPLATE.parse_date(value)
    except InvoiceProcessingError:
        return
    else:
        # None or a date-like are the only allowed happy paths.
        assert result is None or hasattr(result, "year"), (
            f"parse_date returned {type(result).__name__}, expected date-like or None"
        )


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
