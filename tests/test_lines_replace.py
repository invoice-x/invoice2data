"""Per-sub-field `replace` in the lines parser (issue #497, Jopie01)."""

from typing import Any

from invoice2data.extract.parsers import lines


class _Template:
    """Minimal template stub: identity type coercion."""

    def coerce_type(self, value: Any, target: str) -> Any:
        return value


CONTENT = "1 ABC PS 2\n2 DEF M 3\n"
LINE_RE = r"(?P<pos>\d+)\s+(?P<name>\S+)\s+(?P<uom>\S+)\s+(?P<qty>\d+)"


def _parse(replace: Any) -> list[dict[str, Any]]:
    settings = {"line": LINE_RE, "line_separator": r"\n", "replace": replace}
    return lines.parse_block(_Template(), "lines", settings, CONTENT)


def test_lines_replace_mapping_form() -> None:
    rows = _parse({"uom": [["PS", "unit"], ["M", "meter"]]})
    uoms = [row["uom"] for row in rows]
    assert uoms == ["unit", "meter"]


def test_lines_replace_list_of_single_key_dicts_form() -> None:
    # The YAML style from the issue: a list of single-key mappings.
    rows = _parse([{"uom": [["PS", "unit"], ["M", "meter"]]}])
    assert [row["uom"] for row in rows] == ["unit", "meter"]


def test_lines_without_replace_unchanged() -> None:
    rows = _parse(None)
    assert [row["uom"] for row in rows] == ["PS", "M"]
