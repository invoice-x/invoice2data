"""--output-name - / /dev/stdout streams to stdout instead of a file (#608)."""

import json

import pytest

from invoice2data.output import to_csv
from invoice2data.output import to_json


@pytest.mark.parametrize("name", ["-", "/dev/stdout"])
def test_json_output_to_stdout(name: str, capsys: pytest.CaptureFixture[str]) -> None:
    to_json.write_to_file([{"a": 1, "b": "x"}], name)
    assert json.loads(capsys.readouterr().out) == [{"a": 1, "b": "x"}]


def test_csv_output_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    to_csv.write_to_file([{"amount": 1.0, "desc": "x"}], "-")
    out = capsys.readouterr().out
    assert "amount" in out
    assert "desc" in out


def test_file_output_still_works(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "out"
    to_json.write_to_file([{"a": 1}], str(target))
    assert (tmp_path / "out.json").exists()  # suffix added for real paths
