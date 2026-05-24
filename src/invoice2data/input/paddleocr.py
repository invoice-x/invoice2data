"""PaddleOCR (deep-learning OCR) input module for invoice2data.

Local, trained OCR with very broad language coverage (issue #526). Optional:
install with ``pip install invoice2data[paddleocr]`` (pulls in paddleocr +
paddlepaddle + pypdfium2; model weights download on first use). The OCR engine is
cached after the first call.

PaddleOCR works on images, so PDFs are rendered to page images with pypdfium2
first. The whole document is OCR'd; there is no area-restricted mode. The result
parser handles both the PaddleOCR 2.x (``[box, (text, score)]``) and 3.x
(``{"rec_texts": [...]}``) shapes defensively.
"""

import logging
from functools import lru_cache
from typing import Any


logger = logging.getLogger(__name__)


def paddleocr_available() -> bool:
    """Return whether the optional ``paddleocr`` package is importable.

    Returns:
        bool: True if PaddleOCR can be imported.
    """
    try:
        import paddleocr  # noqa: F401
    except ImportError:
        return False
    return True


#: Backend availability check (see input.__interface__).
is_available = paddleocr_available

#: PaddleOCR OCRs the whole document; it has no area-restricted mode.
SUPPORTS_AREA = False


@lru_cache(maxsize=4)
def _get_ocr(lang: str = "en") -> Any:
    """Build and cache a PaddleOCR engine for a language (weights load lazily).

    Args:
        lang (str): PaddleOCR language code. Defaults to "en".

    Returns:
        Any: A ``PaddleOCR`` instance.
    """
    from paddleocr import PaddleOCR

    return PaddleOCR(lang=lang)


def _page_arrays(path: str) -> list[Any]:
    """Render a PDF's pages to image arrays with pypdfium2.

    Args:
        path (str): Path to the PDF file.

    Returns:
        list[Any]: One rendered page image (numpy array) per page.
    """
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(path)
    try:
        return [page.render(scale=2).to_numpy() for page in pdf]
    finally:
        pdf.close()


def _extract_text(result: Any) -> str:
    """Pull plain text out of a PaddleOCR result (2.x or 3.x shape).

    Args:
        result (Any): The value returned by ``PaddleOCR.ocr``.

    Returns:
        str: One detected line per output line.
    """
    texts: list[str] = []
    for page in result or []:
        if isinstance(page, dict) and "rec_texts" in page:  # PaddleOCR 3.x
            texts.extend(str(text) for text in page["rec_texts"])
            continue
        # PaddleOCR 2.x: each entry is ``[box, (text, score)]``.
        texts.extend(
            str(entry[1][0])
            for entry in page or []
            if isinstance(entry, (list, tuple))
            and len(entry) >= 2
            and isinstance(entry[1], (list, tuple))
            and entry[1]
        )
    return "\n".join(texts)


def to_text(
    path: str, area_details: dict[str, Any] | None = None, **kwargs: Any
) -> str:
    """Extract text from a PDF or image with PaddleOCR.

    Args:
        path (str): Path to the PDF or image file.
        area_details (dict[str, Any] | None): Ignored (PaddleOCR has no area mode).
        **kwargs (Any): Optional ``lang`` (PaddleOCR language code, default "en");
            other keys are ignored.

    Returns:
        str: The OCR'd text, or an empty string if PaddleOCR is not available.
    """
    if not paddleocr_available():
        logger.warning(
            "PaddleOCR is not available. "
            "Install with 'pip install invoice2data[paddleocr]'"
        )
        return ""
    ocr = _get_ocr(kwargs.get("lang", "en"))
    sources = _page_arrays(path) if path.lower().endswith(".pdf") else [path]
    pages = [_extract_text(ocr.ocr(source)) for source in sources]
    return "\n".join(page for page in pages if page)
