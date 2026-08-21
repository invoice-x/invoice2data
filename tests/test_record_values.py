"""Static values and defaults for record-producing extractors."""

from typing import Any

from invoice2data.extract.parsers import lines
from invoice2data.extract.parsers.records import apply_static_and_defaults


class _Template:
    def coerce_type(self, value: Any, target: str) -> Any:
        return value


def test_static_and_defaults_preferred_mapping_forms() -> None:
    records = [{"name": "Widget", "qty": ""}, {"name": "Service"}]
    assert apply_static_and_defaults(
        records,
        {
            "static": {"taxes": [{"amount": 21.0}]},
            "defaults": {"qty": 1, "price_unit": 0},
        },
    ) == [
        {"name": "Widget", "qty": 1, "taxes": [{"amount": 21.0}], "price_unit": 0},
        {"name": "Service", "taxes": [{"amount": 21.0}], "qty": 1, "price_unit": 0},
    ]


def test_legacy_record_value_aliases_work_in_modern_lines_parser() -> None:
    rows = lines.parse(
        _Template(),  # type: ignore[arg-type]
        "lines",
        {
            "parser": "lines",
            "start": r"(?m)^Items$",
            "end": r"(?m)^Total$",
            "line": r"(?P<name>\w+)(?:\s+(?P<qty>\d+))?",
            "static_taxes": [{"amount": 9.0}],
            "qty_default": 1,
        },
        "Items\nCoffee 2\nShipping\nTotal\n",
    )
    assert rows == [
        {"name": "Coffee", "qty": "2", "taxes": [{"amount": 9.0}]},
        {"name": "Shipping", "qty": 1, "taxes": [{"amount": 9.0}]},
    ]


def test_modern_rules_inherit_record_values() -> None:
    rows = lines.parse(
        _Template(),  # type: ignore[arg-type]
        "lines",
        {
            "parser": "lines",
            "static": {"taxes": [{"amount": 21.0}]},
            "defaults": {"qty": 1},
            "rules": [
                {
                    "start": r"(?m)^Items$",
                    "end": r"(?m)^Total$",
                    "line": r"(?P<name>\w+)",
                }
            ],
        },
        "Items\nService\nTotal\n",
    )
    assert rows == [{"name": "Service", "taxes": [{"amount": 21.0}], "qty": 1}]


def test_no_newline_and_append_on_line_are_opt_in_lines_options() -> None:
    rows = lines.parse_block(
        _Template(),  # type: ignore[arg-type]
        "lines",
        {
            "first_line": r"ITEM (?P<name>\w+)",
            "line": r"QTY (?P<qty>\d+)",
            "line_separator": r"\n",
            "no_newline_fields": ["name"],
            "append_on_line": True,
        },
        "ITEM One\nQTY 1\nITEM Two\nQTY 2\n",
    )
    assert rows == [{"name": "One", "qty": "1"}, {"name": "Two", "qty": "2"}]


def test_no_newline_fields_concatenates_selected_continuations() -> None:
    rows = lines.parse_block(
        _Template(),  # type: ignore[arg-type]
        "lines",
        {
            "first_line": r"ITEM (?P<name>\w+)",
            "line": r"MORE (?P<name>\w+)",
            "last_line": r"QTY (?P<qty>\d+)",
            "line_separator": r"\n",
            "no_newline_fields": ["name"],
        },
        "ITEM One\nMORE Extra\nQTY 1\n",
    )
    assert rows == [{"name": "OneExtra", "qty": "1"}]
