"""Tesseract OCR backend with the binaries + subprocess pipeline mocked.

These tests exercise ``input/tesseract.py`` without needing real ``tesseract`` /
ImageMagick / ``pdftotext`` binaries or image fixtures.
"""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from invoice2data.input import tesseract


def test_is_available_true(mocker: "pytest_mock.MockerFixture") -> None:  # type: ignore[name-defined]  # noqa
    mocker.patch("invoice2data.input.tesseract.shutil.which", return_value="/usr/bin/x")
    assert tesseract.is_available() is True


def test_is_available_false_when_convert_missing(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    mocker.patch(
        "invoice2data.input.tesseract.shutil.which",
        side_effect=lambda name: "/usr/bin/tesseract" if name == "tesseract" else None,
    )
    assert tesseract.is_available() is False


def test_imagemagick_cmd_prefers_magick_over_convert(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    """ImageMagick 7's ``magick`` is preferred (cross-platform, works on Windows)."""
    mocker.patch(
        "invoice2data.input.tesseract.shutil.which",
        side_effect=lambda name: f"/usr/bin/{name}",  # both are available
    )
    assert tesseract._imagemagick_cmd() == ["magick"]


def test_imagemagick_cmd_falls_back_to_convert(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    """IM 6 boxes only ship ``convert``; the fallback keeps them working."""
    mocker.patch(
        "invoice2data.input.tesseract.shutil.which",
        side_effect=lambda name: "/usr/bin/convert" if name == "convert" else None,
    )
    assert tesseract._imagemagick_cmd() == ["convert"]


def test_imagemagick_cmd_returns_none_when_neither_present(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    mocker.patch("invoice2data.input.tesseract.shutil.which", return_value=None)
    assert tesseract._imagemagick_cmd() is None


def test_to_text_uses_magick_when_available(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    """Regression: on Windows IM 7 ships as ``magick``.

    ``convert`` clashes with Windows' built-in convert.exe on that platform,
    so the pre-conversion pipeline must invoke ``magick`` when it's available
    instead of the legacy ``convert`` name.
    """
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    popen = _mock_pipeline(mocker)  # `which` returns "/usr/bin/x" for every lookup
    tesseract.to_text(str(pdf))
    im_cmd = next(
        call.args[0]
        for call in popen.call_args_list
        if call.args and call.args[0][0] in {"magick", "convert"}
    )
    assert im_cmd[0] == "magick"


def test_to_text_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        tesseract.to_text(str(tmp_path / "nope.pdf"))


def test_to_text_requires_tesseract(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    mocker.patch("invoice2data.input.tesseract.shutil.which", return_value=None)
    with pytest.raises(OSError, match="tesseract not installed"):
        tesseract.to_text(str(pdf))


def test_to_text_requires_imagemagick(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    mocker.patch(
        "invoice2data.input.tesseract.shutil.which",
        side_effect=lambda name: "/usr/bin/tesseract" if name == "tesseract" else None,
    )
    with pytest.raises(OSError, match="imagemagick not installed"):
        tesseract.to_text(str(pdf))


def _mock_pipeline(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
    output: bytes = b"Extracted invoice text\n",
) -> Any:
    """Mock the binaries lookup, language detection and the Popen pipeline."""
    mocker.patch("invoice2data.input.tesseract.shutil.which", return_value="/usr/bin/x")
    mocker.patch("invoice2data.input.tesseract.get_languages", return_value="eng")
    popen = mocker.patch("invoice2data.input.tesseract.Popen")
    proc = popen.return_value
    proc.communicate.return_value = (output, b"")
    proc.wait.return_value = 0
    return popen


def test_to_text_pdf_pipeline(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    _mock_pipeline(mocker)
    assert tesseract.to_text(str(pdf)) == "Extracted invoice text\n"


def test_to_text_image_pipeline(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    # A non-PDF image skips the ImageMagick pre-conversion step.
    img = tmp_path / "invoice.png"
    img.write_bytes(b"\x89PNG\r\n")
    _mock_pipeline(mocker)
    assert tesseract.to_text(str(img)) == "Extracted invoice text\n"


def test_to_text_with_area_details(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    popen = _mock_pipeline(mocker)
    area = {"f": 1, "l": 1, "r": 100, "x": 0, "y": 0, "W": 600, "H": 200}

    assert tesseract.to_text(str(pdf), area) == "Extracted invoice text\n"

    pdftotext_cmd = next(
        call.args[0]
        for call in popen.call_args_list
        if call.args and call.args[0][0] == "pdftotext"
    )
    assert "-W" in pdftotext_cmd
    assert "600" in pdftotext_cmd  # area values are stringified into the command


def test_to_text_tesseract_timeout_still_returns(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    popen = _mock_pipeline(mocker)
    popen.return_value.wait.side_effect = subprocess.TimeoutExpired("tesseract", 180)
    assert tesseract.to_text(str(pdf)) == "Extracted invoice text\n"


def test_to_text_pdftotext_timeout_returns_empty(
    tmp_path: Path,
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    popen = _mock_pipeline(mocker)
    popen.return_value.communicate.side_effect = subprocess.TimeoutExpired(
        "pdftotext", 180
    )
    assert tesseract.to_text(str(pdf)) == ""  # graceful, not UnboundLocalError


def test_get_languages_parses_list(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    proc = MagicMock()
    proc.stdout = "List of available languages (3):\neng\ndeu\nfra\n"
    mocker.patch("invoice2data.input.tesseract.run", return_value=proc)
    assert set(tesseract.get_languages().split("+")) == {"eng", "deu", "fra"}


def test_get_languages_called_process_error(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    mocker.patch(
        "invoice2data.input.tesseract.run",
        side_effect=subprocess.CalledProcessError(1, "tesseract", output="boom"),
    )
    with pytest.raises(OSError, match="boom"):
        tesseract.get_languages()


def test_get_languages_error_in_output(
    mocker: "pytest_mock.MockerFixture",  # type: ignore[name-defined]  # noqa
) -> None:
    proc = MagicMock()
    proc.stdout = "Error opening data file\n"
    mocker.patch("invoice2data.input.tesseract.run", return_value=proc)
    with pytest.raises(OSError, match="Error opening data file"):
        tesseract.get_languages()
