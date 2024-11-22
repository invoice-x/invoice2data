"""pdminer input module for invoice2data."""

from io import StringIO
from typing import Any
from typing import Dict


def to_text(path: str, **kwargs: Dict[str, Any]) -> str:
    """Wrapper around `pdfminer` to extract text from PDF.

    Args:
        path (str): Path to the PDF file.
        **kwargs (Dict[str, Any]): Keyword arguments to be passed to `pdfminer`.

    Returns:
        str: Extracted text from the PDF.
    """
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter
    from pdfminer.pdfinterp import PDFResourceManager
    from pdfminer.pdfpage import PDFPage

    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    laparams.all_texts = True
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    with open(path, "rb") as fp:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()
        pages = PDFPage.get_pages(
            fp,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=True,
        )
        for page in pages:
            interpreter.process_page(page)
    device.close()
    out = retstr.getvalue()
    retstr.close()
    return out
