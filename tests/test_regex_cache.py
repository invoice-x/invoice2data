"""Tests for the cached regex helpers in invoice2data.extract._regex."""

from invoice2data.extract import _regex


def test_compile_is_cached() -> None:
    _regex.compile.cache_clear()
    first = _regex.compile(r"\d+")
    second = _regex.compile(r"\d+")
    assert first is second  # same compiled object served from the cache
    assert _regex.compile.cache_info().hits >= 1


def test_wrappers_behave_like_re() -> None:
    assert _regex.findall(r"(\d+)", "a1b22") == ["1", "22"]
    assert _regex.search(r"\d+", "ab12").group() == "12"
    assert _regex.search(r"\d+", "abc") is None
    assert _regex.split(r"\s+", "a b  c") == ["a", "b", "c"]
    assert _regex.sub(r"\d", "#", "a1b2") == "a#b#"


def test_engine_is_reported() -> None:
    # Default is stdlib "re"; "regex" when INVOICE2DATA_REGEX_ENGINE=regex.
    assert _regex.ENGINE in {"re", "regex"}
