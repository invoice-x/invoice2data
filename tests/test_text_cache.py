"""Text-extraction memoization avoids re-parsing the same doc/area (#perf)."""

import os
import time
import types
from pathlib import Path

from invoice2data.input import _cached_to_text
from invoice2data.input import extract_text


def _fake_backend(counter: dict[str, int]) -> types.ModuleType:
    """A hashable fake backend module that counts to_text calls."""

    def fake_to_text(path: str, area: dict[str, int] | None = None) -> str:
        counter["n"] += 1
        return f"text-{area}"

    module = types.ModuleType("fake_backend")
    module.to_text = fake_to_text  # type: ignore[attr-defined]
    return module


def test_extract_text_memoizes_by_file_and_area(tmp_path: Path) -> None:
    calls = {"n": 0}
    fake = _fake_backend(calls)
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    _cached_to_text.cache_clear()

    area = {"f": 1, "l": 1, "x": 0, "y": 0, "W": 10, "H": 10}
    first = extract_text(fake, str(pdf), area)
    second = extract_text(fake, str(pdf), area)  # identical -> cached
    assert first == second
    assert calls["n"] == 1  # the 3-shared-area case parses once

    extract_text(fake, str(pdf), {**area, "x": 5})  # different area -> new parse
    assert calls["n"] == 2

    extract_text(fake, str(pdf))  # full text -> separate parse
    assert calls["n"] == 3


def test_extract_text_reparses_when_file_changes(tmp_path: Path) -> None:
    calls = {"n": 0}
    fake = _fake_backend(calls)
    pdf = tmp_path / "y.pdf"
    pdf.write_bytes(b"a")
    _cached_to_text.cache_clear()

    extract_text(fake, str(pdf))
    future = time.time() + 10
    os.utime(pdf, (future, future))  # bump mtime so the cache key changes
    extract_text(fake, str(pdf))
    assert calls["n"] == 2  # changed file is re-parsed
