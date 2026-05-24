"""Verification harness for area (region) extraction.

There were no goldens for area extraction, which blocks safely reworking it (the
"parse once + crop in Python" optimization, #2). These tests lock the current
``pdftotext`` area behavior as the contract any future implementation must keep:
an ``area`` returns ONLY the text inside the requested rectangle. When #2 lands,
add parallel assertions that the Python-crop output satisfies the same checks.
"""

import shutil

import pytest

from invoice2data.input import pdftotext


pytestmark = pytest.mark.skipif(
    shutil.which("pdftotext") is None, reason="pdftotext (poppler) not installed"
)

OYO = "tests/compare/oyo.pdf"
# Top band of page 1 (A4 at r=100 dpi ~ 827x1169 px): just the header region.
TOP_BAND = {"f": 1, "l": 1, "r": 100, "x": 0, "y": 0, "W": 900, "H": 120}


def test_area_returns_only_the_requested_region() -> None:
    full = pdftotext.to_text(OYO)
    top = pdftotext.to_text(OYO, TOP_BAND)

    assert "PAYMENT RECEIPT" in top  # header is inside the band
    assert "Date: 31/12/2017" in top
    assert len(top) < len(full)  # genuinely a smaller region than the full page


def test_area_excludes_content_outside_the_region() -> None:
    full = pdftotext.to_text(OYO)
    top = pdftotext.to_text(OYO, TOP_BAND)

    assert "OYO" in full  # present lower on the page
    assert "OYO" not in top  # but excluded by the top-band crop
