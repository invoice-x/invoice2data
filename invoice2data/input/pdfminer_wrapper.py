# -*- coding: utf-8 -*-
def to_text(path):
    """Wrapper around `pdfminer`.

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
        # python 2
        from StringIO import StringIO
        import sys
        reload(sys)  
        sys.setdefaultencoding('utf8')
    except ImportError:
        from io import StringIO

    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage

    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    laparams.all_texts = True
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    with open(path, 'rb') as fp:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()
        pages = PDFPage.get_pages(
            fp, pagenos, maxpages=maxpages, password=password,
            caching=caching, check_extractable=True)
        for page in pages:
            interpreter.process_page(page)
    device.close()
    str = retstr.getvalue()
    retstr.close()
    return str.encode('utf-8')
