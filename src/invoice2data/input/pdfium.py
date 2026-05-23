"""pypdfium2 input module for invoice2data.

A fast, dependency-light PDF text backend (PDFium bindings). Note that its text
order/spacing differs from poppler's ``pdftotext -layout``, so templates tuned
for pdftotext may need adjustment.
"""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)


def is_available() -> bool:
    """Return whether the optional ``pypdfium2`` package is importable.

    Returns:
        bool: True if ``pypdfium2`` is installed.
    """
    import importlib.util

    return importlib.util.find_spec("pypdfium2") is not None


def to_text(path: str, **kwargs: dict[str, Any]) -> str:
    """Extract text from a PDF using pypdfium2.

    Args:
        path (str): Path to the PDF file.
        **kwargs (dict[str, Any]): Ignored; accepted for backend compatibility.

    Returns:
        str: The extracted text, pages joined by newlines.
    """
    import pypdfium2  # type: ignore[import-untyped]

    document = pypdfium2.PdfDocument(path)
    try:
        pages = [
            document[index].get_textpage().get_text_bounded()
            for index in range(len(document))
        ]
    finally:
        document.close()
    text = "\n".join(pages)
    logger.debug("Text extraction made with pypdfium2")
    return text
