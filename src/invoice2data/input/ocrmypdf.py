"""OCRmyPDF input module for invoice2data."""

import logging
import tempfile
from pathlib import Path
from typing import Any

from . import pdftotext


logger = logging.getLogger(__name__)


def ocrmypdf_available() -> bool:
    """Checks if the ocrmypdf module is available.

    Returns:
        bool: True if ocrmypdf is available, False otherwise.
    """
    try:
        import ocrmypdf  # noqa: F401
    except ImportError:
        return False
    return True


SUPPORTS_AREA = True
#: Backend availability check (see input.__interface__).
is_available = ocrmypdf_available


# Default options for redo-ocr to act as a fallback when pdftotext fails
OPTIONS_DEFAULT = {
    "redo_ocr": True,
    "optimize": 0,
    "output_type": "pdf",
    "fast_web_view": 0,
}

#: Common OCRmyPDF pre-processing knobs. Any of these may be passed through
#: ``input_reader_config`` / ``pre_conf`` -- they are forwarded verbatim to
#: ``ocrmypdf.ocr`` -- to clean up noisy scans: ``deskew``, ``clean``,
#: ``clean_final``, ``rotate_pages``, ``remove_background``, ``optimize`` (0-3,
#: image/size optimization) and ``oversample`` (target DPI). A recommended
#: starting set for scanned receipts (spread it into ``input_reader_config``):
RECOMMENDED_SCAN_OPTIONS = {
    "deskew": True,
    "clean": True,
    "rotate_pages": True,
}


def to_text(
    path: str,
    area_details: dict[str, Any] | None = None,
    input_reader_config: dict[str, Any] | None = None,
) -> str:
    """Pre-processes PDF files with ocrmypdf before PDFtotext parsing.

    Ensures OCRmyPDF is installed before attempting to use it.
    If OCRmyPDF is not available, logs a warning and returns an empty string.

    Args:
        path (str): Path to the PDF invoice file.
        area_details (dict[str, Any] | None, optional): Details about the area to extract. Defaults to None.
        input_reader_config (dict[str, Any] | None, optional): Settings forwarded
            to ``ocrmypdf.ocr`` -- e.g. pre-processing knobs like ``deskew`` /
            ``clean`` / ``rotate_pages`` / ``optimize`` (see
            :data:`RECOMMENDED_SCAN_OPTIONS`). Defaults to None.

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
        return pdftotext.to_text(pre_proc_output, area_details)
    return ""


def pre_process_pdf(path: str, pre_conf: dict[str, Any] | None = None) -> str | None:
    """Pre-process a PDF with ocrmypdf, returning the cleaned PDF path.

    The output is a deskewed/cleaned/optimized, text-layered PDF -- usually
    smaller than the original. Callers (e.g. an Odoo integration) can use the
    returned path to **attach or replace the stored file** for size savings, not
    just to feed pdftotext. Writes to a unique temp file unless ``pre_conf``
    sets ``output_file``. Logs a warning if ocrmypdf is not available.

    Args:
        path (str): Path to the PDF invoice file.
        pre_conf (dict[str, Any] | None, optional): Settings forwarded to
            ``ocrmypdf.ocr`` (merged over :data:`OPTIONS_DEFAULT`); pass
            pre-processing knobs here (see :data:`RECOMMENDED_SCAN_OPTIONS`).
            Defaults to None.

    Returns:
        str | None: Path to the processed (cleaned, smaller) PDF, or None if
            processing fails.
    """
    if not ocrmypdf_available():
        logger.warning("ocrmypdf is not available. Install with 'pip install ocrmypdf'")
        return None

    import ocrmypdf

    ocrmypdf_conf = OPTIONS_DEFAULT.copy()
    if pre_conf:
        ocrmypdf_conf.update(pre_conf)
    logger.debug("ocrmypdf config settings: %s", ocrmypdf_conf)

    if "output_file" not in ocrmypdf_conf:
        # Unique temp dir per call so concurrent files with the same name do not
        # collide; the cleaned PDF persists for the caller to read or save.
        out_dir = tempfile.mkdtemp(prefix="invoice2data_ocrmypdf_")
        ocrmypdf_conf["output_file"] = str(Path(out_dir) / Path(path).name)
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
        assert isinstance(pre_proc_output, str)
        return pre_proc_output  # Return the output file path
    logger.warning("ocrmypdf failed, stopping processing of this file")
    return None
