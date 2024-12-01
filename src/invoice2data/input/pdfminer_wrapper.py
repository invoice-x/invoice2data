"""pdminer input module for invoice2data."""

from io import StringIO
from typing import Any
from typing import Dict
from typing import Set


def to_text(path: str, **kwargs: Dict[str, Any]) -> str:
    """Wrapper around `pdfminer` to extract text from PDF.

    Args:
        path (str): Path to the PDF file.
        **kwargs (Dict[str, Any]): Keyword arguments to be passed to `pdfminer`.

    Returns:
        str: Extracted text from the PDF.
    """
    from pdfminer.converter import TextConverter  # type: ignore[import-not-found]
    from pdfminer.layout import LAParams  # type: ignore[import-not-found]
    from pdfminer.pdfinterp import PDFPageInterpreter  # type: ignore[import-not-found]
    from pdfminer.pdfinterp import PDFResourceManager
    from pdfminer.pdfpage import PDFPage  # type: ignore[import-not-found]

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
        pagenos: Set[int] = set()
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
