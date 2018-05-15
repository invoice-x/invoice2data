# -*- coding: utf-8 -*-
def to_text(path):
    """Wraps Tesseract OCR.

    Parameters
    ----------
    path : str
        path of electronic invoice in JPG or PNG format

    Returns
    -------
    extracted_str : str
        returns extracted text from image in JPG or PNG format

    """
    import subprocess

    convert = "convert -density 350 %s -depth 8 tiff:-" % (path)
    p1 = subprocess.Popen(convert.split(' '), stdout=subprocess.PIPE)

    p2 = subprocess.Popen("tesseract stdin stdout".split(' '),
                          stdin=p1.stdout, stdout=subprocess.PIPE)
    out, err = p2.communicate()

    extracted_str = out

    return extracted_str
