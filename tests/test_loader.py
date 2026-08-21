import os
import shutil
import unittest
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import ordered_load
from invoice2data.extract.loader import read_templates


pytestmark = pytest.mark.windows_strict


@pytest.fixture
def templatedirectory() -> Generator[Path, None, None]:
    templatedirectory = Path("tests/templatedirectory/")
    templatedirectory.mkdir(parents=True)

    yield templatedirectory

    shutil.rmtree(templatedirectory, ignore_errors=True)


def test_default_templates_are_loaded() -> None:
    templates = read_templates()

    builtin_tpl_folder = "./src/invoice2data/extract/templates"
    qty_templ_files = sum(len(files) for _, _, files in os.walk(builtin_tpl_folder))

    print("Amount of loaded templates %s" % len(templates))
    print("Amount of template files %s" % qty_templ_files)
    assert len(templates) == qty_templ_files
    assert all(isinstance(template, InvoiceTemplate) for template in templates)


def test_templates_stream_loader() -> None:
    tpl_stream = (
        '[{"issuer":"first biz", "name": "first template", "department":"purchase", "parser":"static", "value":'
        ' "NL82338015B01", "keywords": ["Receipt", "va.nl"]}, {"issuer":"second biz", "name": "2nd template",'
        ' "department":"purchase", "parser":"static", "value": "NL828015B01", "keywords": ["Receipt", "viavia.com"]}]'
    )

    templates = ordered_load(stream=tpl_stream)

    print("Amount of stream loaded templates %s" % len(templates))
    assert len(templates) == 2
    assert all(isinstance(template, InvoiceTemplate) for template in templates)


def test_templates_yaml_stream_loader() -> None:
    # A YAML array of templates, e.g. fetched from a DB column.
    yaml_stream = (
        "- issuer: first biz\n"
        "  name: first template\n"
        "  parser: static\n"
        "  value: NL82338015B01\n"
        "  keywords: [Receipt, va.nl]\n"
        "- issuer: second biz\n"
        "  name: 2nd template\n"
        "  parser: static\n"
        "  value: NL828015B01\n"
        "  keywords: [Receipt, viavia.com]\n"
    )

    templates = ordered_load(stream=yaml_stream, loader=yaml.safe_load)

    assert len(templates) == 2
    assert all(isinstance(template, InvoiceTemplate) for template in templates)
    assert templates[0]["keywords"] == ["Receipt", "va.nl"]


class MyTestCase(unittest.TestCase):
    def test_templates_invalid_stream_loader(self) -> None:
        invalid_tpl_stream = (
            ',,,[{"issuer":"first biz", "name": "first template", "department":"purchase", "parser":"static", "value":'
            ' "NL82338015B01", "keywords": ["Receipt", "va.nl"]}, {"issuer":"second biz", "name": "2nd template",'
            ' "department":"purchase", "parser":"static", "value": "NL828015B01", "keywords": ["Receipt",'
            ' "viavia.com"]}]'
        )

        with self.assertLogs("", level="DEBUG") as cm:
            ordered_load(stream=invalid_tpl_stream)
            print(cm.output)
        self.assertEqual(
            cm.output,
            [
                "WARNING:invoice2data.extract.loader:Failed to load template stream\nExpecting value: line"
                " 1 column 1 (char 0)"
            ],
        )


def test_default_templates_and_stream_loaded() -> None:
    tpl_stream = (
        '[{"issuer":"first biz", "name": "first template", "department":"purchase", "parser":"static", "value":'
        ' "NL82338015B01", "keywords": ["Receipt", "va.nl"]}, {"issuer":"second biz", "name": "2nd template",'
        ' "department":"purchase", "parser":"static", "value": "NL828015B01", "keywords": ["Receipt", "viavia.com"]}]'
    )

    stream_templates = ordered_load(stream=tpl_stream)

    print("Amount of stream loaded templates %s" % len(stream_templates))
    templates = read_templates()
    builtin_tpl_folder = "./src/invoice2data/extract/templates"
    qty_templ_files = sum(len(files) for _, _, files in os.walk(builtin_tpl_folder))

    print("Amount of default loaded templates %s" % len(templates))
    templates += stream_templates
    assert len(templates) == qty_templ_files + 2
    assert all(isinstance(template, InvoiceTemplate) for template in templates)
    print(templates)


def test_template_with_missing_keywords_is_not_loaded(
    templatedirectory: Path,
) -> None:
    yamlfile = templatedirectory / "template_with_missing_keywords.yml"
    yamlfile.write_text(template_with_missing_keywords, encoding="utf-8")

    templates = read_templates(str(templatedirectory))
    assert templates == []


def test_empty_yaml_template_is_skipped(
    templatedirectory: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Issue #721: an empty YAML template must not crash the loader.

    ``yaml.safe_load('')`` returns ``None`` and the loader then did
    ``tpl["template_name"] = name`` -> ``TypeError: 'NoneType' object does
    not support item assignment``. Now guarded with a None-check + warning.
    """
    (templatedirectory / "empty.yaml").write_text("", encoding="utf-8")

    with caplog.at_level("WARNING"):
        templates = read_templates(str(templatedirectory))

    assert templates == []
    assert "Skipping empty template: empty.yaml" in caplog.text


def test_empty_json_template_is_skipped(
    templatedirectory: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An empty ``.json`` file goes through a different path than empty YAML.

    ``json.loads('')`` raises ``ValueError``, which the loader already caught
    and warned about pre-#721. Kept as a separate test so a future JSON-loader
    refactor can't quietly regress the empty-file case there either.
    """
    (templatedirectory / "empty.json").write_text("", encoding="utf-8")

    with caplog.at_level("WARNING"):
        templates = read_templates(str(templatedirectory))

    assert templates == []
    assert "empty.json" in caplog.text


def test_template_name_is_yaml_filename(templatedirectory: Path) -> None:
    yamlfile = templatedirectory / "thisnameisimportant.yml"
    yamlfile.write_text(template_with_single_special_char, encoding="utf-8")

    templates = read_templates(str(templatedirectory))

    assert templates[0]["template_name"] == "thisnameisimportant.yml"


def test_template_with_single_specialchar_is_loaded(
    templatedirectory: Path,
) -> None:
    yamlfile = templatedirectory / "specialchartemplate.yml"
    yamlfile.write_text(template_with_single_special_char, encoding="utf-8")

    templates = read_templates(str(templatedirectory))

    assert templates[0]["fields"]["single_specialchar"]["value"] == "ä"


def test_template_with_keyword_is_not_list(templatedirectory: Path) -> None:
    yamlfile = templatedirectory / "keywordnotlist.yml"
    yamlfile.write_text(template_keyword_not_list, encoding="utf-8")

    tpl = read_templates(str(templatedirectory))
    assert tpl[0]["keywords"] == ["Basic Test"]


def test_template_with_exclude_keyword_is_not_list(
    templatedirectory: Path,
) -> None:
    yamlfile = templatedirectory / "excludekeywordnotlist.yml"
    yamlfile.write_text(template_exclude_keyword_not_list, encoding="utf-8")

    tpl = read_templates(str(templatedirectory))
    assert tpl[0]["exclude_keywords"] == ["Exclude_this"]


def test_template_bad_yaml_format_not_loaded(templatedirectory: Path) -> None:
    yamlfile = templatedirectory / "template_bad_yaml.yml"
    yamlfile.write_text(template_bad_yaml, encoding="utf-8")

    tpl = read_templates(str(templatedirectory))
    assert tpl == [], "Bad Yaml Template is loaded!"


template_with_missing_keywords = """
fields:
  foo:
   parser: static
    value: bar
"""


template_with_single_special_char = """
keywords:
  - Basic Test
fields:
  single_specialchar:
    parser: static
    value: ä
"""


template_keyword_not_list = """
keywords: Basic Test
"""


template_exclude_keyword_not_list = """
keywords: Basic Test
exclude_keywords: Exclude_this
"""


template_bad_yaml = """
keywords: Basic Test
exclude_keywords Exclude_this
options:
  language: EN
"""


def test_read_templates_memoizes_across_calls() -> None:
    """Repeat `read_templates()` calls skip the disk read (memoized by folder+mtime)."""
    from invoice2data.extract.loader import _read_templates_cached

    _read_templates_cached.cache_clear()

    # First call populates the cache.
    read_templates()
    hits_before = _read_templates_cached.cache_info().hits
    read_templates()
    hits_after = _read_templates_cached.cache_info().hits
    assert hits_after == hits_before + 1, (
        "read_templates() should hit the cache on the second identical call; "
        f"cache_info(): {_read_templates_cached.cache_info()}"
    )


def test_read_templates_returned_list_is_a_defensive_copy() -> None:
    """Mutating the returned list must not corrupt other callers' cached view."""
    from invoice2data.extract.loader import _read_templates_cached

    _read_templates_cached.cache_clear()
    first = read_templates()
    original_len = len(first)
    first.pop()  # mutate the returned list

    second = read_templates()
    assert len(second) == original_len, (
        "Mutating the returned list must not shrink the cached view"
    )


def test_read_templates_mtime_change_busts_cache(templatedirectory: Path) -> None:
    """A file mtime change (rewrite) invalidates the memoization signature."""
    import time

    from invoice2data.extract.loader import _read_templates_cached

    _read_templates_cached.cache_clear()
    (templatedirectory / "t.yml").write_text(
        "issuer: A\nkeywords: [x]\n", encoding="utf-8"
    )
    tpls_first = read_templates(str(templatedirectory))
    assert len(tpls_first) == 1
    assert tpls_first[0]["issuer"] == "A"

    # Rewrite with a different issuer; sleep 10 ms so mtime_ns differs.
    time.sleep(0.01)
    (templatedirectory / "t.yml").write_text(
        "issuer: B\nkeywords: [x]\n", encoding="utf-8"
    )
    tpls_second = read_templates(str(templatedirectory))
    assert tpls_second[0]["issuer"] == "B", (
        "Cache should have been invalidated when the file was rewritten"
    )


def test_non_string_keyword_is_rejected_with_yaml_quoting_hint(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #743: a keyword that isn't a string crashes ``matches_input``.

    PhilippFeO's crash was reached via ``exclude_keywords: [invoice id:]``
    which the (older) PyYAML he was using parsed as
    ``[{'invoice id': None}]``. Newer / CSafe-loader PyYAML rejects that
    YAML as a plain-scalar error, so we test the loader defence directly
    (the same shape can reach the loader via ``ordered_load`` from a DB
    column or JSON payload, both of which allow inline mappings).
    """
    from invoice2data.extract.loader import prepare_template

    result = prepare_template(
        {
            "template_name": "trap.yml",
            "keywords": ["Acme"],
            "exclude_keywords": [{"invoice id": None}],
        }
    )
    assert result is None, "non-string keyword must be rejected"

    # The warning identifies the file, the field, the observed type and the
    # YAML-quoting hint so a template author can fix it without spelunking.
    log = caplog.text
    assert "trap.yml" in log
    assert "exclude_keywords" in log
    assert "dict" in log
    assert "quoted" in log


def test_quoted_yaml_keyword_ending_in_colon_loads_normally(
    templatedirectory: Path,
) -> None:
    """The properly-quoted form (`- 'invoice id:'`) works as expected."""
    (templatedirectory / "ok.yml").write_text(
        "issuer: t\nkeywords: [Acme]\nexclude_keywords:\n  - 'invoice id:'\n",
        encoding="utf-8",
    )
    templates = read_templates(str(templatedirectory))
    assert len(templates) == 1
    assert templates[0]["exclude_keywords"] == ["invoice id:"]
