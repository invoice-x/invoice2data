"""pypdfium2 input module for invoice2data.

A fast, dependency-light PDF text backend (Google's PDFium bindings). Its text
order/spacing differs from poppler's ``pdftotext -layout`` (PDFium has no layout
mode), and area extraction is not supported (PDFium uses a different coordinate
system). Layout- or area-sensitive templates should pin
``input_module: pdftotext``.
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


def to_text(
    path: str, area_details: dict[str, Any] | None = None, **kwargs: Any
) -> str:
    """Extract text from a PDF using pypdfium2.

    Args:
        path (str): Path to the PDF file.
        area_details (dict[str, Any] | None): Unsupported by this backend
            (PDFium uses a different coordinate system); a warning is logged and
            the value is ignored. Pin ``input_module: pdftotext`` on area
            templates.
        **kwargs (Any): Ignored; accepted for backend compatibility.

    Returns:
        str: The extracted text, pages joined by newlines.
    """
    if area_details is not None:
        logger.warning(
            "pypdfium2 does not support area extraction; ignoring area_details"
        )

    import pypdfium2

    document = pypdfium2.PdfDocument(path)
    try:
        pages = [
            document[index].get_textpage().get_text_bounded()
            for index in range(len(document))
        ]
    finally:
        document.close()
    logger.debug("Text extraction made with pypdfium2")
    return _post_process("\n".join(pages))


def _post_process(text: str) -> str:
    r"""Normalise pypdfium2 text artifacts for template matching.

    PDFium emits carriage returns and, on some documents, zero-width
    non-characters (e.g. around hyphenated line breaks). Templates and the line
    parser work in terms of ``\n``, so normalise line endings to ``\n`` and
    drop the stray zero-width markers that only confuse regex matching.

    Args:
        text (str): Raw text returned by pypdfium2.

    Returns:
        str: Text with ``\n`` line endings and no zero-width markers.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # U+FEFF (BOM / zero-width no-break space) and U+FFFE (non-character).
    return text.replace("﻿", "").replace("￾", "")
