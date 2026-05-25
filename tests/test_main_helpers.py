"""Helpers in invoice2data.__main__: log formatters, template path, module pin."""

import json
import logging

import pytest

from invoice2data.__main__ import ColorLogFormatter
from invoice2data.__main__ import JsonLogFormatter
from invoice2data.__main__ import PlainLogFormatter
from invoice2data.__main__ import _default_template_path
from invoice2data.__main__ import _preferred_module
from invoice2data.__main__ import _run_new_template
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.input import pdftotext


def _record(msg: str, level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord("invoice2data", level, __file__, 1, msg, None, None)


def _template(input_module: str) -> InvoiceTemplate:
    return InvoiceTemplate(
        {
            "template_name": "t",
            "keywords": ["x"],
            "exclude_keywords": [],
            "input_module": input_module,
        }
    )


def test_default_template_path_slugifies_issuer() -> None:
    assert _default_template_path({"issuer": "ACME Corp, Inc."}) == "acme-corp-inc.yml"


def test_default_template_path_fallback() -> None:
    assert _default_template_path({"issuer": ""}) == "template.yml"


def test_preferred_module_unknown_is_ignored(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        assert _preferred_module(_template("nope"), used=pdftotext) is None
    assert "unknown input_module" in caplog.text


def test_preferred_module_unavailable_is_ignored(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import invoice2data.__main__ as main_module

    monkeypatch.setattr(main_module, "is_available", lambda module: False)
    with caplog.at_level(logging.WARNING):
        assert _preferred_module(_template("pdfium"), used=pdftotext) is None
    assert "unavailable" in caplog.text


def test_color_log_formatter_includes_message() -> None:
    out = ColorLogFormatter().format(_record("hello", logging.ERROR))
    assert "hello" in out


def test_plain_log_formatter_is_ansi_free() -> None:
    out = PlainLogFormatter().format(_record("plain message"))
    assert "plain message" in out
    assert "\x1b[" not in out  # no ANSI escape sequences


def test_json_log_formatter_emits_one_json_object() -> None:
    payload = json.loads(JsonLogFormatter().format(_record("json msg", logging.WARNING)))
    assert payload["level"] == "WARNING"
    assert payload["message"] == "json msg"
    assert payload["name"] == "invoice2data"


def test_run_new_template_exits_when_no_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import invoice2data.__main__ as main_module

    monkeypatch.setattr(main_module, "_sample_text", lambda *a, **k: "")
    with pytest.raises(SystemExit):
        _run_new_template("missing.pdf", use_ai=False, template_out=None, input_module=None)
