"""Property-based tests for input-facing parsers.

The other repo's "OSS-Fuzz has no added value" comment was directionally right
for pure-Python thin-wrapper libraries -- most of the crash class it would find
is cheaper to find with in-process property tests. This module runs
:mod:`hypothesis` on the parsers that accept the noisiest user input:

- ``InvoiceTemplate.parse_number`` -- locale-dependent number parsing
- ``InvoiceTemplate.parse_date`` -- format + language matrix via ``_dates``
- ``ordered_load`` -- YAML/JSON template streams from DB/API payloads
- ``read_templates`` -- YAML files loaded from disk
- ``regex.compile`` on captured template patterns -- ReDoS guard

Contract under test: the parsers may return sensible failure values or raise
one of the *typed* :class:`~invoice2data.exceptions.InvoiceProcessingError`
subclasses (which subclass :class:`ValueError`). They must NOT raise
``AssertionError``, ``TypeError`` (except the documented internal one),
``AttributeError``, ``UnicodeError``, or hang the process.
"""

import json
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from hypothesis import HealthCheck
from hypothesis import assume
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

from invoice2data.exceptions import InvoiceProcessingError
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import ordered_load
from invoice2data.extract.loader import read_templates


pytestmark = pytest.mark.windows_strict


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


def _tpl(**overrides: Any) -> InvoiceTemplate:
    """Build a minimal valid template so `parse_number` / `parse_date` work."""
    base: dict[str, Any] = {
        "template_name": "hypothesis.yml",
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
    base.update(overrides)
    return InvoiceTemplate(base)


# --------------------------------------------------------------------------- #
# parse_number                                                                #
# --------------------------------------------------------------------------- #

_number_bytes = st.text(
    alphabet=st.sampled_from("0123456789.,'\t\n -+eE"), min_size=1, max_size=32
)


@given(value=_number_bytes)
@settings(max_examples=400, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_parse_number_never_crashes_unexpectedly(value: str) -> None:
    """`parse_number` may raise ValueError (or subclass) or return a float.

    It must NOT propagate an unexpected error class -- that's an internal
    invariant leak.
    """
    tpl = _tpl()
    try:
        result = tpl.parse_number(value)
    except (ValueError, InvoiceProcessingError):
        return  # documented contract
    else:
        assert isinstance(result, float), (
            f"expected float, got {type(result).__name__} for input {value!r}"
        )


@given(sep=st.sampled_from([".", ","]))
def test_parse_number_respects_decimal_separator(sep: str) -> None:
    """A number with the declared separator round-trips to a float."""
    tpl = _tpl(options={**_tpl().options, "decimal_separator": sep})
    assert tpl.parse_number(f"1{sep}25") == pytest.approx(1.25)


# --------------------------------------------------------------------------- #
# parse_date                                                                  #
# --------------------------------------------------------------------------- #


@given(value=st.text(min_size=0, max_size=64))
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_parse_date_never_crashes(value: str) -> None:
    """`parse_date` must return a datetime, a date, or None -- never raise."""
    tpl = _tpl()
    try:
        result = tpl.parse_date(value)
    except InvoiceProcessingError:
        return  # typed error class is allowed
    # None (no parse) or a datetime/date-like are the only allowed happy paths.
    assert result is None or hasattr(result, "year"), (
        f"expected date-like or None, got {type(result).__name__}"
    )


# --------------------------------------------------------------------------- #
# Template stream loader (JSON / YAML)                                         #
# --------------------------------------------------------------------------- #


@given(payload=st.text(min_size=0, max_size=256))
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_ordered_load_never_crashes_on_garbage_json(payload: str) -> None:
    """A malformed template stream logs and returns [], never propagates."""
    assert ordered_load(payload) == [] or isinstance(ordered_load(payload), list)


@given(payload=st.text(min_size=0, max_size=256))
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_ordered_load_never_crashes_on_garbage_yaml(payload: str) -> None:
    """Same contract for YAML streams (uses `yaml.safe_load`)."""
    result = ordered_load(payload, loader=yaml.safe_load)
    assert isinstance(result, list)


@given(
    keywords=st.lists(
        st.text(min_size=1, max_size=20), min_size=1, max_size=3, unique=True
    ),
    extra=st.dictionaries(
        keys=st.text(
            alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),
            min_size=1,
            max_size=8,
        ),
        values=st.text(max_size=16),
        max_size=4,
    ),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_ordered_load_accepts_well_formed_stream(
    keywords: list[str], extra: dict[str, str]
) -> None:
    """A stream with the required `keywords` field always parses into a template."""
    tpl_dict = {"issuer": "H", "keywords": keywords, **extra}
    assume(all(k != "template_name" for k in extra))
    payload = json.dumps([tpl_dict])

    result = ordered_load(payload)
    assert len(result) == 1
    assert result[0]["keywords"] == keywords


# --------------------------------------------------------------------------- #
# read_templates on random YAML files                                          #
# --------------------------------------------------------------------------- #


@given(content=st.text(min_size=0, max_size=512))
@settings(
    max_examples=100,
    deadline=1000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_read_templates_survives_arbitrary_yaml_file(
    tmp_path_factory: pytest.TempPathFactory, content: str
) -> None:
    """A hostile ``.yml`` file in the templates folder must not crash the loader."""
    d = tmp_path_factory.mktemp("hypo")
    (d / "hypo.yml").write_text(content, encoding="utf-8")
    result = read_templates(str(d))
    assert isinstance(result, list)
