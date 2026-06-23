"""Contract tests for the input-backend interface (input/__interface__.py)."""

from invoice2data.input import INPUT_MODULES
from invoice2data.input import available_modules
from invoice2data.input import is_available
from invoice2data.input import supports_area


def test_registry_not_empty() -> None:
    assert INPUT_MODULES
    assert "pdftotext" in INPUT_MODULES


def test_backends_conform_to_interface() -> None:
    for name, module in INPUT_MODULES.items():
        assert callable(getattr(module, "to_text", None)), f"{name} missing to_text"
        assert isinstance(supports_area(module), bool)
        assert isinstance(is_available(module), bool)


def test_supports_area_flags() -> None:
    assert supports_area(INPUT_MODULES["pdftotext"]) is True
    assert supports_area(INPUT_MODULES["tesseract"]) is True
    assert supports_area(INPUT_MODULES["ocrmypdf"]) is True
    assert supports_area(INPUT_MODULES["text"]) is False
    assert supports_area(INPUT_MODULES["pdfplumber"]) is False


def test_available_modules_is_subset() -> None:
    avail = available_modules()
    assert set(avail).issubset(set(INPUT_MODULES))
    # the plain-text backend has no optional dependency -> always available
    assert "text" in avail
