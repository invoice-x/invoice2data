"""pdfplumber input module for invoice2data."""

from logging import getLogger
from typing import Any
from typing import Dict


logger = getLogger(__name__)


def to_text(path: str, **kwargs: Dict[str, Any]) -> str:
    """Wrapper around `pdfplumber` to extract text from PDF.

    Args:
        path (str): path of the pdf
        **kwargs (Dict[str, Any]): Keyword arguments to be passed to `pdfminer`.

    Returns:
        str: extracted text from pdf
    """
    try:
        import pdfplumber
    except ImportError:
        logger.debug("Cannot import pdfplumber")

    raw_text = ""
    raw_text = raw_text.encode(encoding="UTF-8")
    with pdfplumber.open(path, laparams={"detect_vertical": True}) as pdf:
        pages = []
        for pdf_page in pdf.pages:
            pages.append(
                pdf_page.extract_text(
                    layout=True,
                    use_text_flow=True,
                    x_tolerance=6,
                    y_tolerance=4,
                    keep_blank_chars=True,
                )  # y_tolerance=6, dirty Fix for html table problem
            )
        res = {
            "all": "\n\n".join(pages),
            "first": pages and pages[0] or "",
        }
    logger.debug("Text extraction made with pdfplumber")

    raw_text = res_to_raw_text(res)
    return raw_text


def res_to_raw_text(res):
    # we need to convert result to raw text:
    raw_text_dict = res
    raw_text = raw_text_dict["first"] or raw_text_dict["all"]
    return raw_text
