import shutil
from pathlib import Path

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

    assert len(templates) == 165
    assert all(isinstance(template, InvoiceTemplate) for template in templates)


def test_template_with_missing_keywords_raises_valueerror(templatedirectory: Path):
    yamlfile = templatedirectory / "specialchartemplate.yml"
    yamlfile.write_text(template_with_missing_keywords, encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        read_templates(str(templatedirectory))

    assert "keywords" in str(exc)


def test_template_name_is_yaml_filename(templatedirectory: Path):
    yamlfile = templatedirectory / "thisnameisimportant.yml"
    yamlfile.write_text(template_with_single_special_char, encoding="utf-8")

    templates = read_templates(str(templatedirectory))

    assert templates[0]["template_name"] == "thisnameisimportant"


def test_template_with_single_specialchar_is_loaded(templatedirectory: Path):
    yamlfile = templatedirectory / "specialchartemplate.yml"
    yamlfile.write_text(template_with_single_special_char, encoding="utf-8")

    templates = read_templates(str(templatedirectory))

    assert templates[0]["fields"]["single_specialchar"]["value"] == "ä"


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
