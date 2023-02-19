# -*- coding: utf-8 -*-

import logging
import tempfile

from pathlib import Path

from . import pdftotext

logger = logging.getLogger(__name__)


def have_ocrmypdf():
    try:
        import ocrmypdf  # noqa: F401
    except ImportError:
        return False
    return True


# Default options redo-ocr
# to act as a fallback when pdftotext fails
OPTIONS_DEFAULT = {
    "redo_ocr": True,
    "optimize": 0,
    "output_type": "pdf",
    "fast_web_view": 0,
}


def to_text(path, area_details: dict = None, input_reader_config: dict = {}):

    """
    Pre-process PDF files with ocrmypdf.
    Before sending them to the pdftotext parser.

    Before usage make sure you have the dependencies installed.

    Parameters
    ----------
    path : str
        path of electronic invoice in PDF format

    Returns
    -------
    extracted_str : str
        returns extracted text from pdf

    """

    if not have_ocrmypdf():
        logger.warning("Cannot import ocrmypdf")
        return ""

    logger.debug("input_reader_config received from main are, *%s*", input_reader_config)

    pre_proc_output = pre_process_pdf(path, pre_conf=input_reader_config)

    if pre_proc_output:
        extracted_str = pdftotext.to_text(pre_proc_output, area_details)
    else:
        return ""

    return extracted_str


def pre_process_pdf(path, pre_conf: dict = None):

    """
    Pre-process PDF files with ocrmypdf.
    Before sending them to the pdftotext parser.

    Before usage make sure you have the dependencies installed.

    Parameters
    ----------
    path : str
        path of electronic invoice in PDF format

    Returns
    -------
    extracted_str : str
        returns extracted text from pdf

    Notes
    -------
    *output_file* can be same as input same to overwrite it.

    For all the available options of ocrmypdf refer to:
    https://ocrmypdf.readthedocs.io/en/latest/api.html#reference

    Advanced example using custom settings for ocrmypdf and unpaper submodule
    control of unpaper settings only works with clean-final or clean

    unpaper_args =  "--pre-rotate -90,"

    pre_conf = {
    "output_file": "test_unpaper_rotate.pdf"
    "clean-final": True,
    "redo_ocr": False,
    "force-ocr": True,
    "unpaper_args": unpaper_args,
    }

    """

    try:
        import ocrmypdf
    except ImportError:
        logger.warning("Cannot import ocrmypdf")

    ocrmypdf_conf = OPTIONS_DEFAULT.copy()

    # Merge the called arguments with defaults
    ocrmypdf_conf.update(pre_conf)
    logger.debug("ocrmypdf config settings are: *%s*", ocrmypdf_conf)

    # Set output_file to temp folder, if it's not specified.
    if "output_file" not in ocrmypdf_conf.keys():
        inputfile = Path(path)
        filename = inputfile.name

        TMP_FOLDER = str(tempfile.gettempdir()) + "/"
        ocrmypdf_conf["output_file"] = TMP_FOLDER + filename
        logger.debug("no output_file specified, using temp file *%s*", ocrmypdf_conf["output_file"])

    logger.debug("OPTIONS !!!!, *%s*", ocrmypdf_conf)

    # try to silence the large amount of debug loggs
    logging.getLogger("ocrmypdf").setLevel(logging.WARNING)
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("ocrmypdf._pipeline").setLevel(logging.WARNING)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    logging.getLogger("ocrmypdf.helpers").setLevel(logging.WARNING)

    exit_code = ocrmypdf.ocr(path, **ocrmypdf_conf)
    if exit_code == 0:
        logger.info("Text extraction made with ocrmypdf")
    else:
        logger.warning("ocrmypdf failed, stop the processing of this file")
        return None

    pre_proc_output = ocrmypdf_conf["output_file"]
    logger.debug("ocrmypdf was called with output file!!!!, *%s*", pre_proc_output)

    return pre_proc_output
