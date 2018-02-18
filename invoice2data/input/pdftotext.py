# -*- coding: utf-8 -*-
def to_text(path):
    import subprocess
    import logging as logger
    import shutil
    from distutils import spawn #py2 compat

    """
    Wrapper around Poppler pdftotext.
    """

    if spawn.find_executable("pdftotext"): #shutil.which('pdftotext'):
        out, err = subprocess.Popen(
            ["pdftotext", '-layout', '-enc', 'UTF-8', path, '-'],
            stdout=subprocess.PIPE).communicate()
        return out
    else:
        raise EnvironmentError('pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/')
