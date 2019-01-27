# -*- coding: utf-8 -*-
import platform


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
    from distutils import spawn

    # Check for dependencies. Needs Tesseract and Imagemagick installed.
    if not spawn.find_executable('tesseract'):
        raise EnvironmentError('tesseract not installed.')
    if not spawn.find_executable('convert'):  # Please remember that on Windows exists C:\Windows\System32\convert.exe and have the same name as ImageMagick tool
        raise EnvironmentError('imagemagick not installed.')

    is_shell_active = platform.system() == "Windows"  # ImageMagick on Windows require shell=True for working
    # convert = "convert -density 350 %s -depth 8 tiff:-" % (path)
    convert = ['convert', '-density', '350', path, '-depth', '8', 'png:-']
    p1 = subprocess.Popen(convert, stdout=subprocess.PIPE, shell=is_shell_active)

    tess = ['tesseract', 'stdin', 'stdout']
    p2 = subprocess.Popen(tess, stdin=p1.stdout, stdout=subprocess.PIPE)

    out, err = p2.communicate()

    extracted_str = out

    return extracted_str
