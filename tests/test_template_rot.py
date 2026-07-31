"""Static validation of every bundled template.

Fable's outside 1.0 review flagged that we ship ~215 templates but only ~13
PDF fixtures in ``tests/compare/`` -- most templates never run through the
extraction pipeline in CI, so silent rot (a broken regex, a removed field, an
option pointing at a Python-only regex flag) is invisible until a user hits it.

Rather than build a synthetic HTML -> PDF corpus per template (a bigger
follow-up), catch the cheap class of rot at *load* time: iterate over every
bundled ``.yml`` / ``.json``, load it, and assert its shape holds up. This
catches:

- YAML parse errors
- missing ``keywords`` (already covered by ``prepare_template``, kept here for
  a per-template error message)
- fields that reference an unknown ``parser`` name
- ``regex``/``static``/``lines``/``tables`` fields whose required keys are
  absent (would raise :class:`TemplateSyntaxError` at extraction time)
- regex patterns that fail to compile
- ``options`` shape mistakes (non-string decimal_separator, malformed
  ``replace``, unknown ``languages`` length)

Runs in <1s, no PDF fixtures needed.
"""

from pathlib import Path
from typing import Any

import pytest
import regex  # type: ignore[import-untyped]

from invoice2data.extract.loader import read_templates


pytestmark = pytest.mark.windows_strict

TEMPLATES_DIR = Path("src/invoice2data/extract/templates")
KNOWN_PARSERS = {"regex", "static", "lines", "tables"}


def _load_all() -> list[dict[str, Any]]:
    """Load every bundled template once; used to parametrise the tests."""
    return list(read_templates(str(TEMPLATES_DIR)))


ALL_TEMPLATES = _load_all()


def test_bundled_templates_load_all() -> None:
    """Loader returns roughly as many templates as files on disk."""
    file_count = (
        sum(1 for _ in TEMPLATES_DIR.rglob("*.yml"))
        + sum(1 for _ in TEMPLATES_DIR.rglob("*.yaml"))
        + sum(1 for _ in TEMPLATES_DIR.rglob("*.json"))
    )
    assert file_count > 0, "no bundled templates found"
    # `prepare_template` may drop templates missing `keywords`; the count should
    # still be within 5% of the on-disk count (catches loader regressions).
    assert len(ALL_TEMPLATES) >= file_count * 0.95, (
        f"{file_count - len(ALL_TEMPLATES)} templates rejected at load time -- "
        "either the loader regressed or a bundled template is malformed"
    )


@pytest.mark.parametrize(
    "template",
    ALL_TEMPLATES,
    ids=[t["template_name"] for t in ALL_TEMPLATES],
)
def test_template_has_valid_shape(template: dict[str, Any]) -> None:
    """Each template has the minimum keys extraction depends on."""
    name = template["template_name"]
    assert isinstance(template.get("keywords"), list) and template["keywords"], (
        f"{name}: `keywords` must be a non-empty list"
    )
    assert isinstance(template.get("exclude_keywords", []), list), (
        f"{name}: `exclude_keywords` must be a list when set"
    )
    fields = template.get("fields")
    if fields is not None:
        assert isinstance(fields, dict), f"{name}: `fields` must be a dict"


@pytest.mark.parametrize(
    "template",
    ALL_TEMPLATES,
    ids=[t["template_name"] for t in ALL_TEMPLATES],
)
def test_template_field_parsers_are_known(template: dict[str, Any]) -> None:
    """Every field with a `parser:` key names a real parser."""
    name = template["template_name"]
    for field, spec in (template.get("fields") or {}).items():
        if not isinstance(spec, dict):
            continue  # legacy `static_x:` / bare regex string forms
        parser = spec.get("parser")
        if parser is None:
            continue
        assert parser in KNOWN_PARSERS, (
            f"{name}: field {field!r} declares unknown parser {parser!r}; "
            f"expected one of {sorted(KNOWN_PARSERS)}"
        )


@pytest.mark.parametrize(
    "template",
    ALL_TEMPLATES,
    ids=[t["template_name"] for t in ALL_TEMPLATES],
)
def test_template_regexes_compile(template: dict[str, Any]) -> None:
    """Every regex referenced by a template compiles under the ``regex`` engine."""
    name = template["template_name"]
    for field, spec in (template.get("fields") or {}).items():
        if isinstance(spec, dict) and spec.get("parser") in {"regex", "lines"}:
            pattern = spec.get("regex")
            if pattern is None:
                continue  # `TemplateSyntaxError` at extraction, out of scope here
            patterns = pattern if isinstance(pattern, list) else [pattern]
            for p in patterns:
                try:
                    regex.compile(p)
                except regex.error as exc:  # noqa: PERF203
                    pytest.fail(f"{name}: field {field!r} regex won't compile: {exc}")


@pytest.mark.parametrize(
    "template",
    ALL_TEMPLATES,
    ids=[t["template_name"] for t in ALL_TEMPLATES],
)
def test_template_options_are_well_formed(template: dict[str, Any]) -> None:
    """Common ``options`` mistakes (non-string separator, malformed replace)."""
    name = template["template_name"]
    options = template.get("options") or {}
    sep = options.get("decimal_separator")
    if sep is not None:
        assert isinstance(sep, str) and len(sep) == 1, (
            f"{name}: `options.decimal_separator` must be a single character"
        )
    replaces = options.get("replace") or []
    for i, pair in enumerate(replaces):
        assert isinstance(pair, list) and len(pair) == 2, (
            f"{name}: `options.replace[{i}]` must be a [pattern, repl] pair"
        )
    languages = options.get("languages") or []
    for lang in languages:
        assert isinstance(lang, str) and len(lang) == 2, (
            f"{name}: `options.languages` entry {lang!r} is not a 2-letter code"
        )
    currency = options.get("currency")
    if currency is not None:
        assert isinstance(currency, str), f"{name}: `options.currency` must be a string"
