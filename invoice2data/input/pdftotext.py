# -*- coding: utf-8 -*-
def to_text(path):
    """Wrapper around Poppler pdftotext.

    Parameters
    ----------
    path : str
        path of electronic invoice in PDF

    Returns
    -------
    out : str
        returns extracted text from pdf

    Raises
    ------
    EnvironmentError:
        If pdftotext library is not found
    """
    import subprocess
    import logging as logger
    import shutil
    from distutils import spawn #py2 compat

    if spawn.find_executable("pdftotext"): #shutil.which('pdftotext'):
        out, err = subprocess.Popen(
            ["pdftotext", '-layout', '-enc', 'UTF-8', path, '-'],
            stdout=subprocess.PIPE).communicate()
        return out
    else:
        raise EnvironmentError('pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/')
