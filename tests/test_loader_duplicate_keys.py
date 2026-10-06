from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

from invoice2data.extract.loader import ordered_load
from invoice2data.extract.loader import read_templates


pytestmark = pytest.mark.windows_strict


@pytest.mark.parametrize("source", ["file", "stream"])
@pytest.mark.parametrize(
    ("mapping", "key", "line"),
    [
        ("issuer: First\nissuer: Second\n", "issuer", 2),
        ("fields:\n  amount: FIRST\n  amount: SECOND\n", "amount", 3),
    ],
)
def test_duplicate_keys_warn_and_keep_last_value(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    source: str,
    mapping: str,
    key: str,
    line: int,
) -> None:
    text = mapping + "keywords: [EXAMPLE]\n"
    if source == "file":
        path = tmp_path / "example.yml"
        path.write_text(text, encoding="utf-8")
        templates = read_templates(str(tmp_path))
        location = str(path)
    else:
        stream = "- " + text.replace("\n", "\n  ").rstrip() + "\n"
        templates = ordered_load(stream, loader=yaml.safe_load)
        location = "<unicode string>"

    assert len(templates) == 1
    if key == "issuer":
        assert templates[0][key] == "Second"
    else:
        assert templates[0]["fields"][key] == "SECOND"
    warnings = [
        r.getMessage() for r in caplog.records if "duplicate key" in r.getMessage()
    ]
    assert len(warnings) == 1
    assert repr(key) in warnings[0]
    assert f"{location}:{line}:" in warnings[0]
    assert "last value" in warnings[0]


def test_merge_overrides_do_not_warn(caplog: pytest.LogCaptureFixture) -> None:
    stream = """\
- keywords: [EXAMPLE]
  defaults: &defaults
    amount: FIRST
  fields:
    <<: [*defaults, {amount: OTHER}]
    amount: SECOND
  copy: *defaults
"""
    templates = ordered_load(stream, loader=yaml.safe_load)
    assert templates[0]["fields"]["amount"] == "SECOND"
    assert templates[0]["copy"]["amount"] == "FIRST"
    assert not caplog.records


def test_duplicate_in_reused_anchor_warns_once(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stream = """\
- keywords: [EXAMPLE]
  defaults: &defaults
    amount: FIRST
    amount: SECOND
  fields:
    <<: *defaults
  copy:
    <<: *defaults
"""
    templates = ordered_load(stream, loader=yaml.safe_load)
    assert templates[0]["fields"]["amount"] == "SECOND"
    assert templates[0]["copy"]["amount"] == "SECOND"
    assert len(caplog.records) == 1
    assert "duplicate key 'amount'" in caplog.text


def test_custom_loader_is_called_unchanged() -> None:
    calls = []

    def custom_loader(stream: str) -> list[dict[str, Any]]:
        calls.append(stream)
        return [{"keywords": ["EXAMPLE"]}]

    assert len(ordered_load("custom input", loader=custom_loader)) == 1
    assert calls == ["custom input"]


@pytest.mark.parametrize("loader", [yaml.safe_load, yaml.full_load])
def test_global_yaml_loaders_are_unchanged(
    loader: Callable[[str], Any], caplog: pytest.LogCaptureFixture
) -> None:
    assert loader("key: first\nkey: second\n") == {"key": "second"}
    assert not caplog.records


@pytest.mark.parametrize(
    "stream",
    ["- ? [unhashable, key]\n  : value\n", "- !!python/object:example.Class {}\n"],
)
def test_invalid_yaml_still_fails_safely(
    stream: str, caplog: pytest.LogCaptureFixture
) -> None:
    assert ordered_load(stream, loader=yaml.safe_load) == []
    assert "Failed to load template stream" in caplog.text
