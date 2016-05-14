# -*- coding: utf-8 -*-
import subprocess
import logging as logger


def to_text(path):
    """
    Wrapper around pdftotext. Fall back if latest version with -table option 
    is unavailable.
    """
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
