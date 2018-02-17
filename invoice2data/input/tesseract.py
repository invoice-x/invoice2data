# -*- coding: utf-8 -*-
def to_text(path):
    """Wraps Tesseract OCR."""
    import subprocess

    convert = "convert -density 350 %s -depth 8 tiff:-" % (path)
    p1 = subprocess.Popen(convert.split(' '), stdout=subprocess.PIPE)

    p2 = subprocess.Popen("tesseract stdin stdout".split(' '),
                          stdin=p1.stdout, stdout=subprocess.PIPE)
    out, err = p2.communicate()

    extracted_str = out.decode('utf-8')

    return extracted_str
