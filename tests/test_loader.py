import os
import shutil

import chardet
import pytest

from invoice2data.extract.loader import (
    detect_template_encoding,
    get_templatefiles,
    read_templates,
)


@pytest.fixture(autouse=True)
def prepare_template(templatefile: str) -> None:
    with open(templatefile, "w", encoding="utf-8") as templatefile:
        templatefile.write(template_with_single_special_char)


@pytest.fixture
def templatedirectory() -> str:
    templatedirectory = os.path.dirname("tests/templatedirectory/")
    os.makedirs(templatedirectory)

    yield templatedirectory

    shutil.rmtree(templatedirectory, ignore_errors=True)


@pytest.fixture
def templatefile(templatedirectory: str) -> str:
    return os.path.join(templatedirectory, "template.yml")


def test_chardet_detect_template_encoding_is_not_utf8(templatefile: str):
    with open(templatefile, "rb") as file:
        detection_result = chardet.detect(file.read())

    assert detection_result["encoding"] != "utf-8"


def test_detect_template_encoding_is_utf8(templatefile: str):
    assert detect_template_encoding(templatefile) == "utf-8"


def test_get_templatefiles(templatedirectory: str, templatefile: str):
    assert get_templatefiles(templatedirectory) == {templatefile: "template.yml"}


def test_template_with_single_specialchar_is_loaded_as_utf8(templatedirectory: str):
    templates = read_templates(templatedirectory)

    assert templates[0]["fields"]["single_specialchar"]["value"] == "ä"


template_with_single_special_char = """
issuer: Basic Test
keywords:
  - Basic Test
fields:
  date:
    parser: regex
    regex: Issue date:\s*(\d{4}-\d{2}-\d{2})
    type: date
  invoice_number:
    parser: regex
    regex: Invoice number:\s*([\d/]+)
  amount:
    parser: regex
    regex: Total:\s*(\d+\.\d\d)
    type: float
  single_specialchar:
    parser: static
    value: ä
options:
  encoding: utf-8
"""
