"""Tests for CSV output: line/tax_lines flattening (A4)."""

import csv
import datetime
import json

from invoice2data.output import to_csv


def _read_csv(path: str) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8") as csv_file:
        return list(csv.reader(csv_file))


def test_csv_json_mode_encodes_arrays(tmp_path) -> None:
    data = [
        {
            "invoice_number": "INV1",
            "amount": 100.0,
            "date": datetime.datetime(2024, 1, 2),
            "lines": [{"name": "Widget", "qty": 2.0}, {"name": "Gadget", "qty": 1.0}],
        }
    ]
    out = str(tmp_path / "out.csv")
    to_csv.write_to_file(data, out)
    rows = _read_csv(out)
    values = dict(zip(rows[0], rows[1], strict=True))
    assert values["date"] == "2024-01-02"
    lines = json.loads(values["lines"])  # the cell is valid JSON, not a Python repr
    assert [item["name"] for item in lines] == ["Widget", "Gadget"]


def test_csv_explode_mode_one_row_per_line(tmp_path) -> None:
    data = [
        {
            "invoice_number": "INV1",
            "lines": [{"name": "Widget", "qty": 2.0}, {"name": "Gadget", "qty": 1.0}],
        }
    ]
    out = str(tmp_path / "out.csv")
    to_csv.write_to_file(data, out, lines_mode="explode")
    rows = _read_csv(out)
    header = rows[0]
    assert "line_name" in header
    assert len(rows) == 3  # header + one row per line item
    assert rows[1][header.index("line_name")] == "Widget"
    assert rows[2][header.index("line_name")] == "Gadget"
    assert rows[1][header.index("invoice_number")] == "INV1"  # repeated per line
