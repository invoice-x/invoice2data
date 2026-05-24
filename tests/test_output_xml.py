"""XML output renders str/number/date/list value types (output/to_xml.py)."""

import datetime
from pathlib import Path

from invoice2data.output import to_xml


def test_xml_handles_all_value_types(tmp_path: Path) -> None:
    data = [
        {
            "issuer": "ACME",  # str
            "amount": 100.0,  # float
            "count": 3,  # int
            "date": datetime.datetime(2024, 1, 1),  # date
            "lines": [{"name": "Widget", "qty": 2}],  # list of dicts
        }
    ]
    target = tmp_path / "out.xml"
    to_xml.write_to_file(data, str(target))

    text = target.read_text(encoding="utf-8")
    assert "<issuer>ACME</issuer>" in text
    assert "<amount>100.0</amount>" in text
    assert "<count>3</count>" in text
    assert "2024-01-01" in text  # date formatted
    assert "<item>" in text  # list element rendered as <item>
    assert "<name>Widget</name>" in text
