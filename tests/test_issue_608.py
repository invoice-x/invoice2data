"""Regression tests for the bug fixes triaged from issue #608."""

import logging

import pytest

from invoice2data.__main__ import _by_priority
from invoice2data.__main__ import _match_template
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import prepare_template
from invoice2data.extract.parsers import regex


def _template(name: str, priority: int) -> InvoiceTemplate:
    prepared = prepare_template(
        {
            "template_name": name,
            "keywords": ["SharedKeyword"],
            "priority": priority,
            "fields": {},
        }
    )
    assert prepared is not None
    return InvoiceTemplate(prepared)


def test_match_template_prefers_higher_priority() -> None:
    low = _template("aaa.yml", 5)  # alphabetically first, lower priority
    high = _template("zzz.yml", 6)  # alphabetically last, higher priority
    text = "Invoice containing SharedKeyword here"

    # Higher priority wins regardless of list/alphabetical order.
    match_lh = _match_template(text, _by_priority([low, high]))
    match_hl = _match_template(text, _by_priority([high, low]))
    assert match_lh is not None
    assert match_hl is not None
    assert match_lh["template_name"] == "zzz.yml"
    assert match_hl["template_name"] == "zzz.yml"


def test_match_template_stable_within_same_priority() -> None:
    first = _template("aaa.yml", 5)
    second = _template("bbb.yml", 5)
    text = "SharedKeyword"
    # Equal priority keeps the original (alphabetical) order.
    matched = _match_template(text, _by_priority([first, second]))
    assert matched is not None
    assert matched["template_name"] == "aaa.yml"


def test_regex_warning_includes_field_name(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="invoice2data.extract.parsers.regex"):
        regex.parse(
            template=None,
            field="invoice_number",
            settings={"regex": 123},  # non-string regex triggers the warning
            content="irrelevant",
        )
    messages = [record.getMessage() for record in caplog.records]
    assert any("invoice_number" in message for message in messages)
    assert all('Field ""' not in message for message in messages)  # not empty
