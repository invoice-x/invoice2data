# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


def to_text(path):
    """Wrapper around `pdfplumber`.
    Parameters
    ----------
    path : str
        path of electronic invoice in PDF
    Returns
    -------
    str : str
        returns extracted text from pdf
    """
    try:
        import pdfplumber
    except ImportError:
        logger.debug("Cannot import pdfplumber")

    raw_text = ""
    raw_text = raw_text.encode(encoding='UTF-8')
    with pdfplumber.open(path, laparams={"detect_vertical": True}) as pdf:
        pages = []
        for pdf_page in pdf.pages:
            pages.append(
                pdf_page.extract_text(
                    layout=True, use_text_flow=True, x_tolerance=6, y_tolerance=4, keep_blank_chars=True
                )  # y_tolerance=6, dirty Fix for html table problem
            )
        res = {
            "all": "\n\n".join(pages),
            "first": pages and pages[0] or "",
        }
    logger.debug("Text extraction made with pdfplumber")

    raw_text = res_to_raw_text(res)
    return raw_text.encode("utf-8")


def res_to_raw_text(res):
    # we need to convert result to raw text:
    raw_text_dict = res
    raw_text = (raw_text_dict["first"] or raw_text_dict["all"])
    return raw_text
