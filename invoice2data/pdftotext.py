# -*- coding: utf-8 -*-
import subprocess
import logging as logger
import shutil


def to_text(path):
    """
    Wrapper around pdftotext. Fall back if latest version with -table option 
    is unavailable.
    """

    if shutil.which('pdftotext'):
        out, err = subprocess.Popen(
            ["pdftotext", '-layout', '-table', '-enc', 'UTF-8', path, '-'],
            stdout=subprocess.PIPE).communicate()
        if not out:
            logger.error('You are using an outdated pdftotext version.' 
                     'Processing PDF tables will be disabled.')
            out, err = subprocess.Popen(
                ["pdftotext", '-layout', '-enc', 'UTF-8', path, '-'],
                stdout=subprocess.PIPE).communicate()
        return out
    else:
        raise EnvironmentError('pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/')
