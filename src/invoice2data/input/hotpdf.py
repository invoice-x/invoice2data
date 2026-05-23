"""hotpdf input module for invoice2data.

hotpdf is a fast pdfminer.six-based reader. Its plain-text output runs words
together more than ``pdftotext -layout``, so templates tuned for pdftotext may
need adjustment.
"""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)


def is_available() -> bool:
    """Return whether the optional ``hotpdf`` package is importable.

    Returns:
        bool: True if ``hotpdf`` is installed.
    """
    import importlib.util

    return importlib.util.find_spec("hotpdf") is not None


def to_text(path: str, **kwargs: dict[str, Any]) -> str:
    """Extract text from a PDF using hotpdf.

    Args:
        path (str): Path to the PDF file.
        **kwargs (dict[str, Any]): Ignored; accepted for backend compatibility.

    Returns:
        str: The extracted text, pages joined by newlines.
    """
    from hotpdf import HotPdf  # type: ignore[import-untyped]

    document = HotPdf(path)
    text = "\n".join(
        document.extract_page_text(index) for index in range(len(document.pages))
    )
    logger.debug("Text extraction made with hotpdf")
    return text
