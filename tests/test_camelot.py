"""Camelot table plugin: extract() logic (camelot mocked) + a real fixture test.

The mocked tests exercise the plugin's logic (rule handling, kwarg forwarding,
table selection, error handling) without the heavy camelot-py/ghostscript/opencv
stack, so they run — and count toward coverage — in CI where camelot is absent.
The fixture test runs only where camelot-py is installed.
"""

import logging
import sys
import types
from typing import Any

import pytest

from invoice2data.extract.plugins import camelot


def _fake_camelot(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
    tables: Any,
) -> Any:
    """Make extract() use an in-process fake camelot module; return its read_pdf."""
    read_pdf = mocker.Mock(return_value=tables)
    mocker.patch.dict(
        sys.modules, {"camelot": types.SimpleNamespace(read_pdf=read_pdf)}
    )
    mocker.patch("invoice2data.extract.plugins.camelot.is_available", return_value=True)
    return read_pdf


def _table(rows: list[list[str]]) -> Any:
    return types.SimpleNamespace(data=rows)


def test_extract_populates_field_with_header(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    read_pdf = _fake_camelot(
        mocker, [_table([["desc", "qty"], ["Widget", "2"], ["Gadget", "5"]])]
    )
    template = {
        "template_name": "t",
        "camelot": {"flavor": "lattice", "pages": "1", "field": "lines"},
    }
    output: dict[str, Any] = {}
    camelot.extract(template, "", output, "x.pdf")

    assert output["lines"] == [
        {"desc": "Widget", "qty": "2"},
        {"desc": "Gadget", "qty": "5"},
    ]
    # Only read_pdf kwargs are forwarded (flavor/pages); field/header/tables are not.
    _, kwargs = read_pdf.call_args
    assert kwargs == {"flavor": "lattice", "pages": "1"}


def test_extract_table_index_selection_without_header(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    _fake_camelot(mocker, [_table([["a"], ["first"]]), _table([["a"], ["second"]])])
    template = {
        "template_name": "t",
        "camelot": {"tables": 1, "field": "lines", "header": False},
    }
    output: dict[str, Any] = {}
    camelot.extract(template, "", output, "x.pdf")
    assert output["lines"] == [{"col_0": "a"}, {"col_0": "second"}]


def test_extract_list_of_rules(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    _fake_camelot(mocker, [_table([["a"], ["1"]])])
    template = {
        "template_name": "t",
        "camelot": [{"field": "lines"}, {"field": "tax_lines"}],
    }
    output: dict[str, Any] = {}
    camelot.extract(template, "", output, "x.pdf")
    assert "lines" in output
    assert "tax_lines" in output


def test_extract_warns_on_unknown_option(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
    caplog: pytest.LogCaptureFixture,
) -> None:
    _fake_camelot(mocker, [_table([["a"], ["1"]])])
    template = {"template_name": "t", "camelot": {"bogus": 1, "field": "lines"}}
    output: dict[str, Any] = {}
    with caplog.at_level(logging.WARNING):
        camelot.extract(template, "", output, "x.pdf")
    assert "unknown option" in caplog.text


def test_extract_read_pdf_failure_is_caught(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    read_pdf = mocker.Mock(side_effect=RuntimeError("boom"))
    mocker.patch.dict(
        sys.modules, {"camelot": types.SimpleNamespace(read_pdf=read_pdf)}
    )
    mocker.patch("invoice2data.extract.plugins.camelot.is_available", return_value=True)
    output: dict[str, Any] = {}
    camelot.extract(
        {"template_name": "t", "camelot": {"flavor": "lattice"}}, "", output, "x.pdf"
    )
    assert output == {}  # exception caught; nothing populated


def test_extract_warns_when_camelot_not_installed(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocker.patch(
        "invoice2data.extract.plugins.camelot.is_available", return_value=False
    )
    output: dict[str, Any] = {}
    with caplog.at_level(logging.WARNING):
        camelot.extract({"template_name": "t", "camelot": {}}, "", output, "x.pdf")
    assert "camelot-py is not" in caplog.text
    assert output == {}


def test_extract_warns_when_no_invoice_file(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocker.patch("invoice2data.extract.plugins.camelot.is_available", return_value=True)
    output: dict[str, Any] = {}
    with caplog.at_level(logging.WARNING):
        camelot.extract({"template_name": "t", "camelot": {}}, "", output, None)
    assert "needs the invoice file path" in caplog.text
    assert output == {}


def test_extract_skips_when_no_body_rows(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    # A header-only table yields no records, so the field is left unset.
    _fake_camelot(mocker, [_table([["only", "header"]])])
    output: dict[str, Any] = {}
    camelot.extract(
        {"template_name": "t", "camelot": {"field": "lines"}}, "", output, "x.pdf"
    )
    assert output == {}


def test_rows_to_records_empty() -> None:
    assert camelot._rows_to_records([], header=True) == []


def test_extract_real_bol_invoice() -> None:
    if not camelot.is_available():
        pytest.skip("camelot-py not installed")
    template = {
        "template_name": "bol",
        "camelot": {"flavor": "stream", "pages": "1", "field": "lines"},
    }
    output: dict[str, Any] = {}
    camelot.extract(template, "", output, "tests/files/camelot-bol100649863.pdf")
    assert isinstance(output["lines"], list)
    assert output["lines"]
    assert all(isinstance(row, dict) for row in output["lines"])
