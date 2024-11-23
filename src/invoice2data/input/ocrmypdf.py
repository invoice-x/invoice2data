"""OCRmyPDF input module for invoice2data."""

import logging
import tempfile
from pathlib import Path

from . import pdftotext


logger = logging.getLogger(__name__)


def ocrmypdf_available() -> bool:
    """Checks if the ocrmypdf module is available.

    Returns:
        bool: True if ocrmypdf is available, False otherwise.
    """
    try:
        import ocrmypdf  # noqa F401

        return True
    except ImportError:
        return False


# Default options for redo-ocr to act as a fallback when pdftotext fails
OPTIONS_DEFAULT = {
    "redo_ocr": True,
    "optimize": 0,
    "output_type": "pdf",
    "fast_web_view": 0,
}


def to_text(
    path: str, area_details: dict = None, input_reader_config: dict = None
) -> str:
    """Pre-processes PDF files with ocrmypdf before PDFtotext parsing.

    Ensures OCRmyPDF is installed before attempting to use it.
    If OCRmyPDF is not available, logs a warning and returns an empty string.

    Args:
        path (str): Path to the PDF invoice file.
        area_details (dict, optional): Details about the area to extract. Defaults to None.
        input_reader_config (dict, optional): Configuration settings for the input reader. Defaults to None.

    Returns:
        str: Extracted text from the PDF, or an empty string if OCRmyPDF is not available or processing fails.
    """
    if input_reader_config is None:
        input_reader_config = {}

    if not ocrmypdf_available():
        logger.warning("ocrmypdf is not available. Install with 'pip install ocrmypdf'")
        return ""

    logger.debug("Input reader config received: %s", input_reader_config)

    pre_proc_output = pre_process_pdf(path, pre_conf=input_reader_config)

    if pre_proc_output:
        extracted_str = pdftotext.to_text(pre_proc_output, area_details)
        return extracted_str
    else:
        return ""


def pre_process_pdf(path: str, pre_conf: dict = None) -> str:
    """Pre-processes PDF files with ocrmypdf before PDFtotext parsing.

    Uses a temporary file for the output by default.
    Logs a warning if ocrmypdf is not available.

    Args:
        path (str): Path to the PDF invoice file.
        pre_conf (dict, optional): Configuration settings for ocrmypdf. Defaults to None.

    Returns:
        str: Path to the processed PDF file, or None if processing fails.

    Notes:
        For available ocrmypdf options, refer to:
        https://ocrmypdf.readthedocs.io/en/latest/api.html#reference
    """
    if not ocrmypdf_available():
        logger.warning("ocrmypdf is not available. Install with 'pip install ocrmypdf'")
        return None

    import ocrmypdf  # Import ocrmypdf here

    ocrmypdf_conf = OPTIONS_DEFAULT.copy()
    if pre_conf:
        ocrmypdf_conf.update(pre_conf)
    logger.debug("ocrmypdf config settings: %s", ocrmypdf_conf)

    if "output_file" not in ocrmypdf_conf:
        inputfile = Path(path)
        filename = inputfile.name
        tmp_folder = str(tempfile.gettempdir()) + "/"
        ocrmypdf_conf["output_file"] = tmp_folder + filename
        logger.debug(
            "No output_file specified, using temp file: %s",
            ocrmypdf_conf["output_file"],
        )

    # Silence excessive debug logs
    logging.getLogger("ocrmypdf").setLevel(logging.WARNING)
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("ocrmypdf._pipeline").setLevel(logging.WARNING)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    logging.getLogger("ocrmypdf.helpers").setLevel(logging.WARNING)

    exit_code = ocrmypdf.ocr(path, **ocrmypdf_conf)
    if exit_code == 0:
        logger.info("Text extraction performed with ocrmypdf")
        pre_proc_output = ocrmypdf_conf["output_file"]
        logger.debug("ocrmypdf output file: %s", pre_proc_output)
        return pre_proc_output
    else:
        logger.warning("ocrmypdf failed, stopping processing of this file")
        return None
