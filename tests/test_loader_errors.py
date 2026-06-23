"""Error/skip paths in the template loader (extract/loader.py)."""

import logging
from pathlib import Path

import pytest

from invoice2data.extract.loader import prepare_template
from invoice2data.extract.loader import read_templates


def test_prepare_template_without_keywords_returns_none(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        result = prepare_template({"template_name": "x.yml", "fields": {}})
    assert result is None
    assert "Missing mandatory 'keywords'" in caplog.text


def test_read_templates_skips_malformed_json(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "bad.json").write_text("{not valid json}", encoding="utf-8")
    (tmp_path / "good.json").write_text(
        '{"keywords": ["ACME"], "fields": {}}', encoding="utf-8"
    )
    with caplog.at_level(logging.WARNING):
        templates = read_templates(str(tmp_path))

    names = {t["template_name"] for t in templates}
    assert "good.json" in names
    assert "bad.json" not in names  # malformed JSON is skipped, not fatal
    assert "bad.json" in caplog.text
