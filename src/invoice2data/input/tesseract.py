# -*- coding: utf-8 -*-
import platform
import shutil
import tempfile
import mimetypes

from subprocess import Popen, PIPE, STDOUT, CalledProcessError, TimeoutExpired
from subprocess import run
from pathlib import Path

from logging import getLogger

logger = getLogger(__name__)


def to_text(path: str, area_details: dict = None):
    """Wraps Tesseract OCR with auto language model.

    Parameters
    ----------
    path : str
        path of electronic invoice in PDF, JPG or PNG format
    area_details : dictionary
        of the format {x: int, y: int, r: int, W: int, H: int}
        used when extracting an area of the pdf rather than the whole document

    Returns
    -------
    extracted_str : str
        returns extracted text from image

    """

    # Check for dependencies. Needs Tesseract and Imagemagick installed.
    current_platform = platform.platform()
    if current_platform.startswith("win32"):
        convert_command_prefix = "magick"
    else:
        convert_command_prefix = "convert"
    if not shutil.which("tesseract"):
        raise EnvironmentError("tesseract not installed.")
    if not shutil.which(convert_command_prefix):
        raise EnvironmentError("imagemagick not installed.")

    language = get_languages()
    logger.debug("tesseract language arg is, %s", language)
    timeout = 180
    # convert the (multi-page) pdf file to a 300dpi png
    convert = [convert_command_prefix] + [
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
    mt = mimetypes.guess_type(path)
    if mt[0] == "application/pdf":
        # tesseract does not support pdf files, pre-processing is needed.
        logger.debug("PDF file detected, start pre-processing by converting to png")
        p1 = Popen(convert, stdout=PIPE)
        tess_input = "stdin"
        stdin = p1.stdout
    else:
        tess_input = path
        stdin = None

    inputfile = Path(path)
    filename = inputfile.stem

    TMP_FOLDER = str(tempfile.gettempdir()) + "/"
    logger.debug("temp dir is, *%s*", TMP_FOLDER)

    tess_cmd = [
        "tesseract",
        "-l",
        language,
        "--oem",
        "3",
        "--psm",
        "6",
        "-c",
        "preserve_interword_spaces=1",
        "-c",
        "textonly_pdf=1",
        tess_input,
        TMP_FOLDER + filename,
        "pdf",
        "txt"
    ]

    logger.debug("Calling tesseract with args, %s", tess_cmd)
    p2 = Popen(tess_cmd, stdin=stdin, stdout=PIPE)

    # Wait for p2 to finish generating the pdf
    try:
        p2.wait(timeout=timeout)
    except TimeoutExpired:
        p2.kill()
        logger.warning("tesseract took too long to OCR - skipping")

    pdftotext_cmd = [
        "pdftotext",
        "-layout",
        "-enc",
        "UTF-8",
    ]
    if area_details is not None:
        # An area was specified
        # Validate the required keys were provided
        assert 'f' in area_details, 'Area r details missing'
        assert 'l' in area_details, 'Area r details missing'
        assert 'r' in area_details, 'Area r details missing'
        assert 'x' in area_details, 'Area x details missing'
        assert 'y' in area_details, 'Area y details missing'
        assert 'W' in area_details, 'Area W details missing'
        assert 'H' in area_details, 'Area H details missing'
        # Convert all of the values to strings
        for key in area_details.keys():
            area_details[key] = str(area_details[key])
        pdftotext_cmd += [
            '-f', area_details['f'],
            '-l', area_details['l'],
            '-r', area_details['r'],
            '-x', area_details['x'],
            '-y', area_details['y'],
            '-W', area_details['W'],
            '-H', area_details['H'],
        ]
    pdftotext_cmd += [TMP_FOLDER + filename + ".pdf", "-"]

    logger.debug("Calling pdfttext with, %s", pdftotext_cmd)
    p3 = Popen(pdftotext_cmd, stdin=p2.stdout, stdout=PIPE)
    try:
        out, err = p3.communicate(timeout=timeout)

        extracted_str = out
    except TimeoutExpired:
        p3.kill()
        logger.warning("pdftotext took too long - skipping")
    return extracted_str.decode('utf-8')


def get_languages():

    def lang_error(output):
        logger.warning = (
            "Tesseract failed to report available languages.\n"
            "Output from Tesseract:\n"
            "-----------\n"
        )
        return
    logger.debug("get lang called")
    args_tess = ['tesseract', '--list-langs']
    try:
        proc = run(
            args_tess,
            text=True,
            stdout=PIPE,
            stderr=STDOUT,
            check=True,
        )
        output = proc.stdout
    except CalledProcessError as e:
        raise EnvironmentError(lang_error(e.output)) from e

    for line in output.splitlines():
        if line.startswith('Error'):
            raise EnvironmentError(lang_error(output))
    _header, *rest = output.splitlines()
    langlist = {lang.strip() for lang in rest}
    return '+'.join(map(str, langlist))
