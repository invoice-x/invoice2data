# -*- coding: utf-8 -*-
# from wand.image import Image as WandImage
from PIL import Image
import pytesseract
import os
import subprocess
import tempfile


def to_text(path):
    """Wraps Tesseract OCR. Not reliable at the moment."""

    tiff_file = tempfile.NamedTemporaryFile(suffix='.tiff')
    FNULL = open(os.devnull, 'w')
    subprocess.call([
        "convert",
        "-density",
        "350",
        path,
        "-depth",
        "8",
        tiff_file.name
        ], stdout=FNULL, stderr=subprocess.STDOUT)

    # TODO: find a way to do this in python?
    # with WandImage(filename=path, resolution=200) as img:
    #     img.compression_quality = 200
    #     img.format='png'
    #     img.save(filename=tempfile)

    extracted_str = pytesseract.image_to_string(Image.open(tiff_file))
    tiff_file.close()
    return extracted_str

    # convert -density 300 file.pdf -depth 8 file.tiff
