"""docTR (deep-learning OCR) input module for invoice2data.

Local, trained OCR that handles scanned/photographed documents well, usually
without manual pre-processing (issue #526). Optional: install with
``pip install invoice2data[doctr]`` (pulls in docTR + a torch backend; the model
weights download on first use). The OCR predictor is cached after the first call.

docTR reads PDFs and images directly (PDF rendering via pypdfium2 under the hood),
so this backend OCRs the whole document and has no area-restricted mode.
"""

import logging
from functools import lru_cache
from typing import Any


logger = logging.getLogger(__name__)


def doctr_available() -> bool:
    """Return whether the optional ``python-doctr`` package is importable.

    Returns:
        bool: True if docTR can be imported.
    """
    try:
        import doctr  # noqa: F401
    except ImportError:
        return False
    return True


#: Backend availability check (see input.__interface__).
is_available = doctr_available

#: docTR OCRs the whole document; it has no area-restricted mode.
SUPPORTS_AREA = False


@lru_cache(maxsize=1)
def _get_model() -> Any:
    """Build and cache the docTR OCR predictor (weights load on first call).

    Returns:
        Any: A pretrained ``ocr_predictor`` instance.
    """
    from doctr.models import ocr_predictor

    return ocr_predictor(pretrained=True)


def _render(result: Any) -> str:
    """Render a docTR result to plain text.

    Args:
        result (Any): The docTR ``Document`` returned by the predictor.

    Returns:
        str: The document text, one detected line per output line.
    """
    render = getattr(result, "render", None)
    if callable(render):
        return str(render())
    # Fallback: rebuild text from the stable export structure.
    lines = [
        " ".join(word["value"] for word in line.get("words", []))
        for page in result.export().get("pages", [])
        for block in page.get("blocks", [])
        for line in block.get("lines", [])
    ]
    return "\n".join(lines)


def to_text(
    path: str, area_details: dict[str, Any] | None = None, **kwargs: Any
) -> str:
    """Extract text from a PDF or image with docTR OCR.

    Args:
        path (str): Path to the PDF or image file.
        area_details (dict[str, Any] | None): Ignored (docTR has no area mode).
        **kwargs (Any): Ignored; accepted for backend-interface compatibility.

    Returns:
        str: The OCR'd text, or an empty string if docTR is not available.
    """
    if not doctr_available():
        logger.warning(
            "docTR is not available. Install with 'pip install invoice2data[doctr]'"
        )
        return ""
    from doctr.io import DocumentFile

    if path.lower().endswith(".pdf"):
        document = DocumentFile.from_pdf(path)
    else:
        document = DocumentFile.from_images(path)
    result = _get_model()(document)
    return _render(result)
