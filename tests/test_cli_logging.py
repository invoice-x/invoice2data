"""Tests for the --no-color and --debug-optimized-str CLI features (#608)."""

import contextlib
import json
import logging

import pytest

from invoice2data.__main__ import JsonLogFormatter
from invoice2data.__main__ import PlainLogFormatter
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import prepare_template


def test_plain_log_formatter_strips_ansi() -> None:
    record = logging.LogRecord(
        name="invoice2data",
        level=logging.INFO,
        pathname="p",
        lineno=1,
        msg="\033[94mhello\033[0m world",
        args=None,
        exc_info=None,
    )
    output = PlainLogFormatter().format(record)
    assert "\033" not in output  # no escape sequences
    assert "hello world" in output


def test_json_log_formatter_emits_valid_json() -> None:
    record = logging.LogRecord(
        name="invoice2data",
        level=logging.WARNING,
        pathname="p",
        lineno=1,
        msg="\033[94mheads up\033[0m",
        args=None,
        exc_info=None,
    )
    data = json.loads(JsonLogFormatter().format(record))
    assert data["level"] == "WARNING"
    assert data["name"] == "invoice2data"
    assert data["message"] == "heads up"  # ANSI stripped
    assert "time" in data


def test_debug_optimized_str_logger_emits(caplog: pytest.LogCaptureFixture) -> None:
    template = InvoiceTemplate(
        prepare_template({"template_name": "t.yml", "keywords": ["Test"], "fields": {}})
    )
    # extract() logs optimized_str early, then raises (no required fields here).
    with (
        caplog.at_level(logging.DEBUG, logger="invoice2data.optimized_str"),
        contextlib.suppress(ValueError),
    ):
        template.extract("Test invoice body", "file.txt", None)

    messages = [record.getMessage() for record in caplog.records]
    assert any("START optimized_str" in message for message in messages)
    assert any("Test invoice body" in message for message in messages)


def test_optimized_str_logger_quiet_at_info(caplog: pytest.LogCaptureFixture) -> None:
    template = InvoiceTemplate(
        prepare_template({"template_name": "t.yml", "keywords": ["Test"], "fields": {}})
    )
    with (
        caplog.at_level(logging.INFO, logger="invoice2data.optimized_str"),
        contextlib.suppress(ValueError),
    ):
        template.extract("Test invoice body", "file.txt", None)

    assert not any("optimized_str" in record.getMessage() for record in caplog.records)
