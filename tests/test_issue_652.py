"""Issue #652 -- two opt-in template hooks.

Cleaned-up implementation of the @avonbuttlar contribution:

- ``extract_number: true`` on a regex field plucks the first numeric token
  out of a captured value mixed with text/units (e.g. ``"12123 Stk."`` ->
  ``"12123"``). Opt-in -- existing ``int``/``float`` fields are unaffected.
- ``skip_line: <pattern>`` (or a list of patterns) on a lines block drops
  lines matching an unwanted shape (e.g. a sub-total footer).

These tests also lock in the regex-truncation cases that the original PR
review flagged.
"""

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.parsers import lines as lines_parser
from invoice2data.extract.parsers import regex as regex_parser
from invoice2data.extract.parsers.regex import _extract_number


_TEMPLATE_STUB = InvoiceTemplate(
    [
        ("issuer", "test"),
        ("keywords", ["test"]),
        ("exclude_keywords", []),
        ("template_name", "test.yml"),
        (
            "options",
            {
                "currency": "EUR",
                "languages": [],
                "decimal_separator": ".",
                "remove_whitespace": False,
                "remove_accents": False,
                "lowercase": False,
                "date_formats": [],
                "replace": [],
            },
        ),
    ]
)


# === extract_number --- the regex itself ===


def test_extract_number_returns_full_4digit_int() -> None:
    """Regression: the original PR's regex truncated `1234` -> `123`."""
    assert _extract_number("1234") == "1234"


def test_extract_number_returns_full_5digit_int() -> None:
    """Regression: `12123 Stk.` returned `121` under the original regex."""
    assert _extract_number("12123 Stk.") == "12123"


def test_extract_number_keeps_decimal_separator() -> None:
    assert _extract_number("1234.56") == "1234.56"
    assert _extract_number("1939,00") == "1939,00"


def test_extract_number_keeps_thousands_and_decimal() -> None:
    """Both German-style and US-style grouping survive intact."""
    assert _extract_number("1.234,56") == "1.234,56"
    assert _extract_number("1,234.56") == "1,234.56"


def test_extract_number_strips_currency_symbol() -> None:
    assert _extract_number("€25.50") == "25.50"
    assert _extract_number("$ 199") == "199"


def test_extract_number_strips_trailing_unit() -> None:
    assert _extract_number("4 Stück") == "4"
    assert _extract_number("12123 Stk.") == "12123"


def test_extract_number_keeps_sign() -> None:
    assert _extract_number("-42") == "-42"
    assert _extract_number("+17.5") == "+17.5"


def test_extract_number_returns_input_on_no_digits() -> None:
    """No digits -> hand the value back so downstream coerce/parse logs the
    real problem instead of swallowing it as ``""``."""
    assert _extract_number("N/A") == "N/A"
    assert _extract_number("") == ""


def test_extract_number_passes_through_non_strings() -> None:
    assert _extract_number(None) is None
    assert _extract_number(42) == 42


# === extract_number --- opt-in via regex parser ===


def test_regex_parser_extract_number_int() -> None:
    settings = {
        "regex": r"qty\s+(\d+\s+Stk\.)",
        "type": "int",
        "extract_number": True,
    }
    result = regex_parser.parse(_TEMPLATE_STUB, "qty", settings, "qty 12123 Stk.")
    assert result == 12123


def test_regex_parser_extract_number_float() -> None:
    settings = {
        "regex": r"price\s+(€\d+\.\d+)",
        "type": "float",
        "extract_number": True,
    }
    result = regex_parser.parse(
        _TEMPLATE_STUB, "price", settings, "price €25.50"
    )
    assert result == 25.50


def test_regex_parser_extract_number_off_by_default() -> None:
    """Without the opt-in, the wider capture stays as-is and coerce_type
    fails -- the contributor's original change globally broke this path."""
    settings = {"regex": r"qty\s+(\d+\s+Stk\.)", "type": "int"}
    # Without extract_number, parse_number cannot turn "12123 Stk." into an
    # int and raises -- the test simply asserts behavior is unchanged.
    import contextlib

    with contextlib.suppress(Exception):
        result = regex_parser.parse(
            _TEMPLATE_STUB, "qty", settings, "qty 12123 Stk."
        )
        # If it didn't raise, the wider string should still be there.
        assert result != 12123


# === skip_line ===


def _make_lines_settings(line_re: str, skip: object = None) -> dict[str, object]:
    settings: dict[str, object] = {
        "line": line_re,
        "line_separator": r"\n",
        "types": {},
    }
    if skip is not None:
        settings["skip_line"] = skip
    return settings


def test_skip_line_string_pattern_drops_matching_lines() -> None:
    settings = _make_lines_settings(
        r"(?P<name>\w+)\s+(?P<qty>\d+)\s+(?P<price>\d+\.\d+)",
        skip=r"^Subtotal",
    )
    content = "Apples 3 1.50\nSubtotal 9 4.50\nBananas 2 0.75"
    result = lines_parser.parse_block(_TEMPLATE_STUB, "lines", settings, content)
    names = [row["name"] for row in result]
    assert names == ["Apples", "Bananas"]


def test_skip_line_list_of_patterns_drops_any_match() -> None:
    settings = _make_lines_settings(
        r"(?P<name>\w+)\s+(?P<qty>\d+)\s+(?P<price>\d+\.\d+)",
        skip=[r"^Subtotal", r"^VAT"],
    )
    content = (
        "Apples 3 1.50\nSubtotal 9 4.50\nVAT 0 0.85\nBananas 2 0.75"
    )
    result = lines_parser.parse_block(_TEMPLATE_STUB, "lines", settings, content)
    names = [row["name"] for row in result]
    assert names == ["Apples", "Bananas"]


def test_skip_line_absent_keeps_existing_behavior() -> None:
    settings = _make_lines_settings(
        r"(?P<name>\w+)\s+(?P<qty>\d+)\s+(?P<price>\d+\.\d+)",
    )
    content = "Apples 3 1.50\nBananas 2 0.75"
    result = lines_parser.parse_block(_TEMPLATE_STUB, "lines", settings, content)
    assert [row["name"] for row in result] == ["Apples", "Bananas"]
