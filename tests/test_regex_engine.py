"""The regex-engine selector honours INVOICE2DATA_REGEX_ENGINE (extract/_regex.py)."""

import importlib

import pytest

from invoice2data.extract import _regex


def test_default_engine_is_stdlib_re() -> None:
    assert _regex.ENGINE == "re"


def test_env_selects_the_regex_package(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INVOICE2DATA_REGEX_ENGINE", "regex")
    try:
        reloaded = importlib.reload(_regex)
        assert reloaded.ENGINE == "regex"
        # The selected engine is API-compatible with stdlib re.
        match = reloaded.search(r"\d+", "abc123")
        assert match is not None
        assert match.group() == "123"
    finally:
        monkeypatch.delenv("INVOICE2DATA_REGEX_ENGINE", raising=False)
        importlib.reload(_regex)  # restore the default (re) engine
    assert _regex.ENGINE == "re"
