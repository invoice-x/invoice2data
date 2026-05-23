"""pdfplumber input module for invoice2data."""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)


def is_available() -> bool:
    """Return whether the optional ``pdfplumber`` package is importable.

    Returns:
        bool: True if ``pdfplumber`` is installed.
    """
    import importlib.util

    return importlib.util.find_spec("pdfplumber") is not None


def to_text(path: str, **kwargs: dict[str, Any]) -> str:
    """Extract text from PDF using pdfplumber.

    Args:
        path (str): Path to the PDF file.
        **kwargs (dict[str, Any]): Keyword arguments to be passed to `pdfplumber`.

    Returns:
        str: Extracted text from the PDF.

    Raises:
        ImportError: If the optional `pdfplumber` dependency is not installed.
    """
    try:
        import pdfplumber  # type: ignore[import-not-found]
    except ImportError:
        logger.error("Cannot import pdfplumber")
        raise

    with pdfplumber.open(path, laparams={"detect_vertical": True}) as pdf:
        raw_text = ""
        for page in pdf.pages:
            # The layout/tolerance params emulate `pdftotext -layout`, which the
            # templates rely on. extract_text() returns None for an empty page.
            raw_text += (
                page.extract_text(
                    layout=True,
                    use_text_flow=True,
                    x_tolerance=6,
                    y_tolerance=4,
                    keep_blank_chars=True,
                    **kwargs,
                )
                or ""
            )
    logger.debug("Text extraction made with pdfplumber")
    return raw_text
