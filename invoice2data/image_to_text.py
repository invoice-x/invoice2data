# from wand.image import Image as WandImage
from PIL import Image
import pytesseract
import os
import subprocess

tempfile = "/tmp/89asdf.tiff"

def to_text(path):

    FNULL = open(os.devnull, 'w')
    subprocess.call(["convert", "-density", "350", path, "-depth", "8", tempfile], stdout=FNULL, stderr=subprocess.STDOUT)
    
    # TODO: find a way to do this in python?
    # with WandImage(filename=path, resolution=200) as img:
    #     img.compression_quality = 200
    #     img.format='png'
    #     img.save(filename=tempfile)

    str = pytesseract.image_to_string(Image.open(tempfile), lang='deu')
    os.remove(tempfile)
    return str

    # convert -density 300 file.pdf -depth 8 file.tiff  