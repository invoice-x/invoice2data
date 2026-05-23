"""pdf-oxide input module for invoice2data.

A fast Rust-based PDF text backend (``pdf_oxide``). Its text order/spacing
differs from poppler's ``pdftotext -layout``, so templates tuned for pdftotext
may need adjustment.
"""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)


def is_available() -> bool:
    """Return whether the optional ``pdf-oxide`` package is importable.

    Returns:
        bool: True if ``pdf_oxide`` is installed.
    """
    import importlib.util

    return importlib.util.find_spec("pdf_oxide") is not None


def to_text(path: str, **kwargs: dict[str, Any]) -> str:
    """Extract text from a PDF using pdf-oxide.

    Args:
        path (str): Path to the PDF file.
        **kwargs (dict[str, Any]): Ignored; accepted for backend compatibility.

    Returns:
        str: The extracted text, pages joined by newlines.
    """
    from pdf_oxide import PdfDocument  # type: ignore[import-untyped]

    document = PdfDocument(path)
    # to_plain_text_all (layout-preserving) scored best in the backend benchmark.
    text: str = document.to_plain_text_all(preserve_layout=True)
    logger.debug("Text extraction made with pdf-oxide")
    return text
