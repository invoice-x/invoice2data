# -*- coding: utf-8 -*-


def to_text(path):
    """Wraps Tesseract OCR.

    Parameters
    ----------
    path : str
        path of electronic invoice in JPG, PNG or PDF format

    Returns
    -------
    extracted_str : str
        returns extracted text from image or PDF file

    """
    import subprocess
    from distutils import spawn

    # Check for dependencies. Needs Tesseract and Imagemagick installed.
    if not spawn.find_executable("tesseract"):
        raise EnvironmentError("tesseract not installed.")
    if not spawn.find_executable("convert"):
        raise EnvironmentError("imagemagick not installed.")

    # convert the (multi-page) pdf file to a 300dpi png
    convert = [
        "convert",
        "-units",
        "PixelsPerInch",
        "-density",
        "350",
        path,
        "-depth",
        "8",
        "-alpha",
        "off",
        "-resample",
        "300x300",
        "-append",
        "png:-",
    ]
    p1 = subprocess.Popen(convert, stdout=subprocess.PIPE)

    tess = ["tesseract", "stdin", "stdout"]
    p2 = subprocess.Popen(tess, stdin=p1.stdout, stdout=subprocess.PIPE)

    out, err = p2.communicate()

    extracted_str = out

    return extracted_str
