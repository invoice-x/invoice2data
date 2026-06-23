"""pypdfium2 input module for invoice2data.

A fast, dependency-light PDF text backend (Google's PDFium bindings). Its text
order/spacing differs from poppler's ``pdftotext -layout`` (PDFium has no layout
mode), so layout-sensitive templates should still pin ``input_module: pdftotext``.
Area (region) extraction is supported in-process via PDFium's
``get_text_bounded``; note its output is not identical to pdftotext's area output,
so an area template targets one backend's text, not both.
"""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)

#: PDFium can extract a bounded region in-process (see _crop_pages).
SUPPORTS_AREA = True


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
        area_details (dict[str, Any] | None): Restrict extraction to a region.
            Keys (pixels at ``r`` dpi, top-left origin): ``f``/``l`` (first/last
            page), ``x``/``y`` (top-left), ``W``/``H`` (size), ``r`` (dpi).
            Defaults to None (whole document).
        **kwargs (Any): Ignored; accepted for backend compatibility.

    Returns:
        str: The extracted text, pages joined by newlines.
    """
    import pypdfium2

    document = pypdfium2.PdfDocument(path)
    try:
        if area_details is not None:
            pages = _crop_pages(document, area_details)
        else:
            pages = [
                document[index].get_textpage().get_text_bounded()
                for index in range(len(document))
            ]
    finally:
        document.close()
    logger.debug("Text extraction made with pypdfium2")
    return _post_process("\n".join(pages))


def _crop_pages(document: Any, area: dict[str, Any]) -> list[str]:
    """Extract each page's text within the area rectangle.

    The area is pixels at dpi ``r`` with a top-left origin (poppler convention);
    PDFium uses points with a bottom-left origin, so the rectangle is scaled
    (``pt = px * 72 / r``) and the y axis is flipped using the page height.

    Args:
        document (Any): An open ``pypdfium2.PdfDocument``.
        area (dict[str, Any]): Keys f, l, r, x, y, W, H.

    Returns:
        list[str]: The cropped text, one entry per page in the range.
    """
    for key in ("f", "l", "r", "x", "y", "W", "H"):
        assert key in area, f"Area {key} details missing"
    first, last = int(area["f"]), int(area["l"])
    factor = 72.0 / float(area["r"])
    x, y = float(area["x"]), float(area["y"])
    width, height = float(area["W"]), float(area["H"])

    pages: list[str] = []
    for index in range(first - 1, min(last, len(document))):
        page = document[index]
        _, page_height = page.get_size()
        left = x * factor
        right = (x + width) * factor
        top = page_height - y * factor
        bottom = page_height - (y + height) * factor
        pages.append(
            page.get_textpage().get_text_bounded(
                left=left, bottom=bottom, right=right, top=top
            )
        )
    return pages


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
