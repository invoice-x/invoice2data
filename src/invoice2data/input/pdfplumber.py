"""pdfplumber input module for invoice2data."""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)


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
            # raw_text += page.extract_text(**kwargs)

            raw_text += page.extract_text(
                layout=True,
                use_text_flow=True,
                x_tolerance=6,
                y_tolerance=4,
                keep_blank_chars=True,
                **kwargs,
            )  # y_tolerance=6, dirty Fix for html table problem

        res = {
            "all": "\n\n".join(
                str(page) for page in pdf.pages
            ),  # Convert pages to strings
            "first": (pdf.pages and str(pdf.pages[0])) or "",  # Convert page to string
        }
    logger.debug("Text extraction made with pdfplumber")

    raw_text = res_to_raw_text([res])
    return raw_text


def res_to_raw_text(res: list[dict[str, Any]]) -> str:
    """Extract raw text from pdfplumber result.

    Args:
        res (list[dict[str, Any]]): Result from pdfplumber.

    Returns:
        str: The raw text extracted from the result.
    """
    raw_text = ""
    for r in res:
        if "text" in r:
            raw_text += r["text"]
    return raw_text
