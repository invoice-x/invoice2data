import shutil
from pathlib import Path

import os
import pytest

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import read_templates


@pytest.fixture
def templatedirectory() -> Path:
    templatedirectory = Path("tests/templatedirectory/")
    templatedirectory.mkdir(parents=True)

    yield templatedirectory

    shutil.rmtree(templatedirectory, ignore_errors=True)


def test_default_templates_are_loaded():
    templates = read_templates()

    builtin_tpl_folder = "./src/invoice2data/extract/templates"
    qty_templ_files = sum(len(files) for _, _, files in os.walk(builtin_tpl_folder))

    print("Amount of loaded templates %s" % len(templates))
    print("Amount of template files %s" % qty_templ_files)
    assert len(templates) == qty_templ_files
    assert all(isinstance(template, InvoiceTemplate) for template in templates)


def test_template_with_missing_keywords_is_not_loaded(templatedirectory: Path):
    yamlfile = templatedirectory / "template_with_missing_keywords.yml"
    yamlfile.write_text(template_with_missing_keywords, encoding="utf-8")

    templates = read_templates(str(templatedirectory))
    assert templates == []


def test_template_name_is_yaml_filename(templatedirectory: Path):
    yamlfile = templatedirectory / "thisnameisimportant.yml"
    yamlfile.write_text(template_with_single_special_char, encoding="utf-8")

    templates = read_templates(str(templatedirectory))

    assert templates[0]["template_name"] == "thisnameisimportant.yml"


def test_template_with_single_specialchar_is_loaded(templatedirectory: Path):
    yamlfile = templatedirectory / "specialchartemplate.yml"
    yamlfile.write_text(template_with_single_special_char, encoding="utf-8")

    templates = read_templates(str(templatedirectory))

    assert templates[0]["fields"]["single_specialchar"]["value"] == "ä"


def test_template_with_keyword_is_not_list(templatedirectory: Path):
    yamlfile = templatedirectory / "keywordnotlist.yml"
    yamlfile.write_text(template_keyword_not_list, encoding="utf-8")

    tpl = read_templates(str(templatedirectory))
    assert tpl[0]["keywords"] == ['Basic Test']


def test_template_with_exclude_keyword_is_not_list(templatedirectory: Path):
    yamlfile = templatedirectory / "excludekeywordnotlist.yml"
    yamlfile.write_text(template_exclude_keyword_not_list, encoding="utf-8")

    tpl = read_templates(str(templatedirectory))
    assert tpl[0]["exclude_keywords"] == ['Exclude_this']


def test_template_bad_yaml_format_not_loaded(templatedirectory: Path):
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
