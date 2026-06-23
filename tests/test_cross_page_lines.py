"""Cross-page lines parsing (#650 / #624 / #359).

Confirms the building blocks for multi-page invoices:

- The lines parser already concatenates description values across multiple
  ``line`` matches (see ``parse_current_row``), so a multi-line description
  bracketed by ``first_line`` / ``last_line`` works as-is.
- ``skip_line`` (now pre-loop, in fd27734) filters repeating page headers /
  footers that would otherwise wrongly match ``first_line`` or ``line``.
- ``end_match: last`` makes ``parse_by_rule`` use the LAST occurrence of the
  ``end`` regex in the ``start``-bounded slice, so a block can span multiple
  pages where the ``end`` pattern repeats per-page (e.g. a footer).
"""

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.parsers import lines as lines_parser


_TPL = InvoiceTemplate(
    [
        ("issuer", "test"),
        ("keywords", ["test"]),
        ("exclude_keywords", []),
        ("template_name", "cross-page.yml"),
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


# === Description spanning multiple text lines (#624 / #359) ===


def test_description_across_multiple_lines_concatenates() -> None:
    """`first_line` captures the SKU + start of description.

    `line` captures description continuation; `last_line` captures the
    amounts. Description is concatenated with newlines (parse_current_row's
    default).
    """
    settings = {
        "line_separator": r"\n",
        "first_line": r"(?m)^(?P<sku>SKU\d+)\s+(?P<name>.+)$",
        "line": r"(?m)^\s{4,}(?P<name>\w[\w\s]*)$",
        "last_line": (
            r"(?m)^\s+(?P<qty>\d+)\s+(?P<price_unit>[\d.]+)\s+"
            r"(?P<price_subtotal>[\d.]+)$"
        ),
    }
    content = (
        "SKU0001 Switch Pro Wireless Controller for\n"
        "    Nintendo Switch Console Wireless\n"
        "    Gamepad\n"
        "     40       18.50            648.00\n"
        "SKU0002 US/EU Wall Charger for DSi AC Adapter\n"
        "    for Nintendo 3DS Power Supply for\n"
        "    3DSXL\n"
        "     1000     0.715            858.00\n"
    )
    rows = lines_parser.parse_block(_TPL, "lines", settings, content)
    assert len(rows) == 2
    assert rows[0]["sku"] == "SKU0001"
    assert "Switch Pro Wireless Controller for" in rows[0]["name"]
    assert "Nintendo Switch Console Wireless" in rows[0]["name"]
    assert "Gamepad" in rows[0]["name"]
    assert rows[0]["qty"] == "40"
    assert rows[0]["price_subtotal"] == "648.00"
    assert rows[1]["sku"] == "SKU0002"
    assert "3DSXL" in rows[1]["name"]


# === skip_line drops repeating page headers (#650) ===


def test_skip_line_drops_repeating_page_headers() -> None:
    """A page-header line that would otherwise match `first_line` is dropped.

    `skip_line` filters it out so the next real item is parsed correctly.
    """
    settings = {
        "line_separator": r"\n",
        "line": r"^(?P<sku>SKU\d+)\s+(?P<name>.+)\s+(?P<qty>\d+)$",
        "skip_line": [
            r"^Acme Corp \| Invoice continued$",
            r"^Page \d+ of \d+$",
        ],
    }
    content = (
        "SKU0001 Widget 3\n"
        "Acme Corp | Invoice continued\n"
        "Page 1 of 2\n"
        "SKU0002 Gadget 7\n"
        "Page 2 of 2\n"
        "SKU0003 Gizmo 2\n"
    )
    rows = lines_parser.parse_block(_TPL, "lines", settings, content)
    assert [r["sku"] for r in rows] == ["SKU0001", "SKU0002", "SKU0003"]
    assert [r["qty"] for r in rows] == ["3", "7", "2"]


# === end_match: last bridges a per-page `end` pattern ===


def test_end_match_first_is_default_and_stops_at_first_end() -> None:
    """Default behavior: `end` matches the FIRST occurrence.

    A per-page footer ends the block prematurely.
    """
    settings = {
        "line_separator": r"\n",
        "start": r"(?m)^ITEMS$",
        "end": r"(?m)^_+\n\s*Total this page",
        "line": r"^(?P<sku>SKU\d+)\s+(?P<qty>\d+)$",
    }
    content = (
        "ITEMS\n"
        "SKU0001 3\n"
        "SKU0002 5\n"
        "________________________________________\n"
        "  Total this page: 8\n"
        "SKU0003 2\n"
        "________________________________________\n"
        "  Total this page: 2\n"
    )
    rows = lines_parser.parse_by_rule(_TPL, "lines", settings, content)
    # Only the first page parses; SKU0003 is past the (first) `end`.
    assert [r["sku"] for r in rows] == ["SKU0001", "SKU0002"]


def test_end_match_last_spans_across_per_page_footers() -> None:
    """`end_match: last` uses the LAST occurrence of `end`.

    Lets the block span all pages even when the `end` pattern repeats.
    """
    settings = {
        "line_separator": r"\n",
        "start": r"(?m)^ITEMS$",
        "end": r"(?m)^_+\n\s*Total this page",
        "end_match": "last",
        "line": r"^(?P<sku>SKU\d+)\s+(?P<qty>\d+)$",
    }
    content = (
        "ITEMS\n"
        "SKU0001 3\n"
        "SKU0002 5\n"
        "________________________________________\n"
        "  Total this page: 8\n"
        "SKU0003 2\n"
        "________________________________________\n"
        "  Total this page: 2\n"
    )
    rows = lines_parser.parse_by_rule(_TPL, "lines", settings, content)
    assert [r["sku"] for r in rows] == ["SKU0001", "SKU0002", "SKU0003"]


def test_end_match_invalid_value_falls_back_to_first() -> None:
    settings = {
        "line_separator": r"\n",
        "start": r"(?m)^ITEMS$",
        "end": r"(?m)^Done$",
        "end_match": "bogus",
        "line": r"(?m)^(?P<sku>SKU\d+)$",
    }
    content = "ITEMS\nSKU0001\nDone\n"
    rows = lines_parser.parse_by_rule(_TPL, "lines", settings, content)
    assert [r["sku"] for r in rows] == ["SKU0001"]
