"""PennyOCR input module for invoice2data.

`PennyOCR <https://pennyocr.com>`_ is a hosted, VLM-based OCR API
($0.75 per 1,000 pages, first 100 pages/month free). This backend uploads the
document and returns the extracted plain text — no local OCR engine, GPU or
system binary required. Handles scanned PDFs, photos and images (PDF, PNG,
JPEG, WebP, TIFF).

Set the ``PENNYOCR_API_KEY`` environment variable (keys from
https://pennyocr.com/dashboard/). Uses only the standard library.
"""

import json
import logging
import os
import uuid
from pathlib import Path
from urllib import request as _request


logger = logging.getLogger(__name__)

API_URL = os.environ.get("PENNYOCR_API_URL", "https://api.pennyocr.com/v1/ocr")
TIMEOUT = float(os.environ.get("PENNYOCR_TIMEOUT", "180"))


def have_pennyocr_key() -> bool:
    return bool(os.environ.get("PENNYOCR_API_KEY"))


#: Backend availability check (see input.__interface__).
is_available = have_pennyocr_key

#: PennyOCR reads the whole document; it has no area-restricted mode.
SUPPORTS_AREA = False


def to_text(path: str, area_details: dict | None = None, **kwargs) -> str:
    """Send a document to the PennyOCR API and return its plain text.

    Args:
        path (str): Path of the invoice (PDF, PNG, JPEG, WebP or TIFF).
        area_details (dict | None): Ignored — this backend reads whole pages.
        **kwargs: Ignored, accepted for interface compatibility.

    Returns:
        str: Extracted text; multipage documents joined by form feeds,
        matching the page separator convention of the pdftotext backend.

    Raises:
        OSError: If the API cannot be reached or rejects the request
            (invalid key, out of credits, unreadable file).
    """
    api_key = os.environ.get("PENNYOCR_API_KEY")
    if not api_key:
        raise OSError("PENNYOCR_API_KEY is not set")
    if area_details is not None:
        logger.warning("pennyocr does not support area extraction; reading whole pages")

    data = Path(path).read_bytes()
    boundary = uuid.uuid4().hex
    filename = Path(path).name.replace('"', "")
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        + data
        + f"\r\n--{boundary}--\r\n".encode()
    )
    req = _request.Request(
        API_URL + "?format=text",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with _request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = json.load(resp)
    except Exception as e:  # urllib raises subclasses of OSError for HTTP errors
        raise OSError(f"PennyOCR request failed: {e}") from e

    logger.debug(
        "pennyocr extracted %s page(s) from %s", payload.get("pages"), filename
    )
    return payload.get("text", "")
