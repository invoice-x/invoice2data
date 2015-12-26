# -*- coding: utf-8 -*-
import subprocess

def to_text(path):
    out, err = subprocess.Popen(["pdftotext", "-layout", '-enc', 'UTF-8', path, '-'], stdout=subprocess.PIPE ).communicate()
    return out
