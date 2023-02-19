import shutil
from pathlib import Path

import pytest

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import read_templates


@pytest.fixture(autouse=True)
def prepare_template(templatefile: Path) -> None:
    templatefile.write_text(template_with_single_special_char, encoding="utf-8")


@pytest.fixture
def templatedirectory() -> Path:
    templatedirectory = Path("tests/templatedirectory/")
    templatedirectory.mkdir(parents=True)

    yield templatedirectory

    shutil.rmtree(templatedirectory, ignore_errors=True)


@pytest.fixture
def templatefile(templatedirectory: Path) -> Path:
    return templatedirectory / "template.yml"


def test_default_templates_are_loaded():
    templates = read_templates()

    assert len(templates) == 165
    assert all(isinstance(template, InvoiceTemplate) for template in templates)


def test_template_with_single_specialchar_is_loaded(templatedirectory: Path):
    templates = read_templates(str(templatedirectory))

    assert templates[0]["fields"]["single_specialchar"]["value"] == "ä"


template_with_single_special_char = """
keywords:
  - Basic Test
fields:
  single_specialchar:
    parser: static
    value: ä
"""
