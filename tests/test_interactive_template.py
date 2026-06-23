"""Interactive `--new-template --interactive` flow (copier-style prompts)."""

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from click.testing import CliRunner

from invoice2data.__main__ import main


SAMPLE = (
    "ACME\n"
    "Invoice No: 2024-001\n"
    "BTW: NL123456789B01\n"  # no dots: keep the field set predictable for the prompts
    "KvK: 12345678\n"
)


def _sample(tmp_path: Path) -> str:
    path = tmp_path / "inv.txt"
    path.write_text(SAMPLE, encoding="utf-8")
    return str(path)


def _written_fields(out: Path) -> dict[str, object]:
    return dict(yaml.safe_load(out.read_text())["fields"])


def test_interactive_accept_all_writes_template(tmp_path: Path) -> None:
    out = tmp_path / "acme.yml"
    result = CliRunner().invoke(
        main,
        [
            "--new-template",
            _sample(tmp_path),
            "--interactive",
            "--template-out",
            str(out),
        ],
        input="\n" * 12,  # keep every field, don't add more, accept the write
    )
    assert result.exit_code == 0, result.output
    fields = _written_fields(out)
    assert "vat" in fields
    assert "partner_coc" in fields
    assert "invoice_number" in fields
    # the VAT cleanup (replace) is carried into the written template
    assert isinstance(fields["vat"], dict)
    assert "replace" in fields["vat"]


def test_interactive_skip_drops_first_field(tmp_path: Path) -> None:
    out = tmp_path / "acme.yml"
    result = CliRunner().invoke(
        main,
        [
            "--new-template",
            _sample(tmp_path),
            "--interactive",
            "--template-out",
            str(out),
        ],
        input="s\n" + "\n" * 12,  # skip the first field (vat), keep the rest
    )
    assert result.exit_code == 0, result.output
    fields = _written_fields(out)
    assert "vat" not in fields
    assert "partner_coc" in fields


def test_interactive_edit_replaces_regex(tmp_path: Path) -> None:
    out = tmp_path / "acme.yml"
    result = CliRunner().invoke(
        main,
        [
            "--new-template",
            _sample(tmp_path),
            "--interactive",
            "--template-out",
            str(out),
        ],
        input="e\nMyVat:(.+)\n" + "\n" * 12,  # edit the first field's regex
    )
    assert result.exit_code == 0, result.output
    vat = _written_fields(out)["vat"]
    regex = vat["regex"] if isinstance(vat, dict) else vat
    assert regex == "MyVat:(.+)"


def test_interactive_add_new_field(tmp_path: Path) -> None:
    out = tmp_path / "acme.yml"
    # keep the 3 detected fields, then add one ("y" + name + regex), then stop + write.
    result = CliRunner().invoke(
        main,
        [
            "--new-template",
            _sample(tmp_path),
            "--interactive",
            "--template-out",
            str(out),
        ],
        input="\n\n\ny\npurchase_order\nPO:(\\d+)\nn\ny\n",
    )
    assert result.exit_code == 0, result.output
    fields = _written_fields(out)
    assert fields.get("purchase_order") == "PO:(\\d+)"
