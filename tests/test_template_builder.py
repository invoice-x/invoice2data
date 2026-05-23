import re

import yaml
from click.testing import CliRunner

from invoice2data.__main__ import main
from invoice2data.ai.template_generator import preview_template
from invoice2data.extract.candidates import find_candidates
from invoice2data.extract.template_builder import field_regex_from_candidate
from invoice2data.extract.template_builder import suggested_template
from invoice2data.extract.template_builder import to_yaml


SAMPLE = "ACME Corp\nInvoice number: INV-42\nDate: 2024-05-07\nTotal: 121.00\n"


def test_suggested_template_builds_fields_and_issuer() -> None:
    template = suggested_template(SAMPLE)
    assert template["issuer"] == "ACME Corp"
    assert template["keywords"] == ["ACME Corp"]
    assert "date" in template["fields"]
    assert "amount" in template["fields"]


def test_suggested_template_regexes_capture_via_preview() -> None:
    template = suggested_template(SAMPLE)
    preview = preview_template(template, SAMPLE)
    assert preview["date"] == "2024-05-07"
    assert preview["amount"] == "121.00"


def test_field_regex_anchors_on_label() -> None:
    amount = next(c for c in find_candidates(SAMPLE) if c.kind == "amount")
    pattern = field_regex_from_candidate(SAMPLE, amount)
    match = re.search(pattern, SAMPLE)
    assert match is not None
    assert match.group(1) == "121.00"


def test_to_yaml_roundtrips() -> None:
    template = {
        "issuer": "ACME",
        "keywords": ["ACME"],
        "fields": {"date": r"Date:\s*(\S+)"},
    }
    assert yaml.safe_load(to_yaml(template)) == template


def test_cli_new_template_writes_yaml(tmp_path) -> None:  # type: ignore[no-untyped-def]
    sample = tmp_path / "sample.txt"
    sample.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "acme.yml"

    result = CliRunner().invoke(
        main,
        ["--new-template", str(sample), "--template-out", str(out)],
        input="y\n",
    )

    assert result.exit_code == 0, result.output
    assert out.exists()
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded["issuer"] == "ACME Corp"
    assert "amount" in loaded["fields"]
