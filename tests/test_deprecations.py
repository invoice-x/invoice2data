"""Tests for 1.0 deprecation warnings."""

from typing import Any

import pytest

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.plugins import lines as lines_plugin


def test_lines_plugin_emits_deprecation_warning() -> None:
    template = InvoiceTemplate(
        {
            "template_name": "deprecation-test.yml",
            "keywords": ["Item"],
            "lines": {
                "start": "Item",
                "end": "Total",
                "line": r"(?P<description>.+)\s+(?P<price>\d+[.,]\d{2})",
            },
        }
    )
    content = "Item\nWidget 1,00\nTotal"
    output: dict[str, Any] = {}
    with pytest.warns(DeprecationWarning, match="deprecated"):
        lines_plugin.extract(template, content, output)
    # behaviour is unchanged: it still extracts the line items
    assert output["lines"]
