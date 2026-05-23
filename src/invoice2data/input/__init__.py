"""Input (text-extraction) backends and their registry.

See `__interface__` for the backend contract. `INPUT_MODULES` maps the stable
backend name (the `--input-reader` value) to its module.
"""

from types import ModuleType

from . import gvision
from . import ocrmypdf
from . import pdfminer_wrapper
from . import pdfplumber
from . import pdftotext
from . import tesseract
from . import text


#: Registry: backend name (the ``--input-reader`` value) -> backend module.
INPUT_MODULES: dict[str, ModuleType] = {
    "pdftotext": pdftotext,
    "tesseract": tesseract,
    "pdfminer": pdfminer_wrapper,
    "pdfplumber": pdfplumber,
    "gvision": gvision,
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


def available_modules() -> dict[str, ModuleType]:
    """Return the registered backends whose dependencies are available.

    Returns:
        dict[str, ModuleType]: Subset of ``INPUT_MODULES`` usable in the
            current environment.
    """
    return {
        name: module for name, module in INPUT_MODULES.items() if is_available(module)
    }
