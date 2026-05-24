"""Tests for per-field data sanitization (``replace``) — issue #497."""

from invoice2data.extract.parsers import regex


def test_field_replace_single_pair_sanitizes_vat() -> None:
    # The motivating case: a simple regex + replace to strip non-word characters.
    settings = {
        "regex": r"VAT NUMBER\s+(\S+)",
        "replace": [r"\W+", ""],
    }
    result = regex.parse(
        template=None,
        field="vat",
        settings=settings,
        content="VAT NUMBER           NL.999,999.999,B01 ",
    )
    assert result == "NL999999999B01"


def test_field_replace_multiple_pairs_applied_in_order() -> None:
    settings = {
        "regex": r"unit:\s+(\S+)",
        "replace": [["PS", "pieces"], [r"\d", ""]],
    }
    result = regex.parse(
        template=None, field="uom", settings=settings, content="unit: PS5"
    )
    # "PS5" -> "pieces5" -> "pieces"
    assert result == "pieces"


def test_field_without_replace_is_unchanged() -> None:
    settings = {"regex": r"ref\s+(\S+)"}
    result = regex.parse(
        template=None, field="ref", settings=settings, content="ref AB.12"
    )
    assert result == "AB.12"


def test_field_replace_applies_to_each_match() -> None:
    settings = {"regex": r"id (\S+)", "replace": [r"\W+", ""]}
    result = regex.parse(
        template=None, field="ids", settings=settings, content="id a.1 and id b.2"
    )
    assert sorted(result) == ["a1", "b2"]
