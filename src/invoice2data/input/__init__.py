"""Input (text-extraction) backends and their registry.

See `__interface__` for the backend contract. `INPUT_MODULES` maps the stable
backend name (the `--input-reader` value) to its module.
"""

from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

from . import doctr
from . import gvision
from . import hotpdf
from . import ocrmypdf
from . import paddleocr
from . import pdfium
from . import pdfminer_wrapper
from . import pdfoxide
from . import pdfplumber
from . import pdftotext
from . import tesseract
from . import text


#: Registry: backend name (the ``--input-reader`` value) -> backend module.
INPUT_MODULES: dict[str, ModuleType] = {
    "pdftotext": pdftotext,
    "pdfium": pdfium,
    "pdfoxide": pdfoxide,
    "tesseract": tesseract,
    "pdfminer": pdfminer_wrapper,
    "pdfplumber": pdfplumber,
    "hotpdf": hotpdf,
    "gvision": gvision,
    "doctr": doctr,
    "paddleocr": paddleocr,
    "text": text,
    "ocrmypdf": ocrmypdf,
}


def supports_area(module: ModuleType) -> bool:
    """Return whether a backend supports area-restricted extraction.

    Args:
        module (ModuleType): An input backend module.

    Returns:
        bool: True if the backend declares ``SUPPORTS_AREA = True``.
    """
    return bool(getattr(module, "SUPPORTS_AREA", False))


def supports_pages(module: ModuleType) -> bool:
    """Return whether a backend can restrict extraction to a page range."""
    return bool(getattr(module, "SUPPORTS_PAGES", False))


def is_available(module: ModuleType) -> bool:
    """Return whether a backend's runtime dependency is available.

    Args:
        module (ModuleType): An input backend module.

    Returns:
        bool: The result of the backend's ``is_available()`` if it defines one,
            otherwise True (the backend is assumed always available).
    """
    checker = getattr(module, "is_available", None)
    return bool(checker()) if callable(checker) else True


@lru_cache(maxsize=128)
def _cached_to_text(
    module: ModuleType,
    invoicefile: str,
    mtime: float | None,
    area_key: tuple[tuple[str, Any], ...] | None,
    pages: tuple[int, int] | None,
) -> str:
    """Memoized backend call (key includes file mtime + area for correctness)."""
    # Keep the established positional ``area`` call compatible with third-party
    # readers. Page-aware readers receive the additional keyword explicitly.
    if pages is None:
        if area_key is None:
            return str(module.to_text(invoicefile))
        return str(module.to_text(invoicefile, dict(area_key)))
    kwargs: dict[str, Any] = {"pages": pages}
    if area_key is not None:
        kwargs["area_details"] = dict(area_key)
    return str(module.to_text(invoicefile, **kwargs))


def parse_pages(value: Any) -> tuple[int, int]:
    """Parse a template's inclusive ``pages`` value (for example ``"2-3"``)."""
    if isinstance(value, int):
        first = last = value
    elif isinstance(value, str):
        parts = value.split("-", maxsplit=1)
        try:
            first = int(parts[0].strip())
            last = int(parts[-1].strip())
        except ValueError as exc:
            raise ValueError("pages must be a page number or an inclusive range such as '2-3'") from exc
    else:
        raise TypeError("pages must be a page number or an inclusive range such as '2-3'")
    if first < 1 or last < first:
        raise ValueError("pages must be positive and ordered, for example '2-3'")
    return first, last


def extract_text(
    module: ModuleType,
    invoicefile: str,
    area: dict[str, Any] | None = None,
    pages: Any = None,
) -> str:
    """Extract text with a backend, memoized per (backend, file, mtime, area).

    Avoids re-parsing the same document within a run -- e.g. when several template
    fields share one ``area``, or the same full text is requested again. The file
    mtime is part of the key so a changed file is re-read.

    Args:
        module (ModuleType): An input backend exposing ``to_text``.
        invoicefile (str): Path to the document.
        area (dict[str, Any] | None): Optional area-restriction passed through.
        pages (int | str | None): Optional inclusive page or page range, such as
            ``2`` or ``"2-3"``. The backend must support page ranges.

    Returns:
        str: The extracted text.
    """
    try:
        mtime: float | None = Path(invoicefile).stat().st_mtime
    except OSError:
        mtime = None
    area_key = tuple(sorted(area.items())) if area else None
    page_range = parse_pages(pages) if pages is not None else None
    if page_range is not None and not supports_pages(module):
        raise ValueError(f"Input backend {module.__name__} does not support page ranges")
    return _cached_to_text(module, invoicefile, mtime, area_key, page_range)


def available_modules() -> dict[str, ModuleType]:
    """Return the registered backends whose dependencies are available.

    Returns:
        dict[str, ModuleType]: Subset of ``INPUT_MODULES`` usable in the
            current environment.
    """
    return {
        name: module for name, module in INPUT_MODULES.items() if is_available(module)
    }
