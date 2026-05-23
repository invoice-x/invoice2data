"""Poppler pdftotext input module for invoice2data."""

import shutil
from pathlib import Path
from typing import Any


SUPPORTS_AREA = True


def is_available() -> bool:
    """Return whether the poppler ``pdftotext`` binary is on the PATH.

    Returns:
        bool: True if ``pdftotext`` can be run.
    """
    return shutil.which("pdftotext") is not None


def to_text(path: str, area_details: dict[str, Any] | None = None) -> str:
    """Extract text from a PDF file using pdftotext.

    Args:
        path (str): Path to the PDF file.
        area_details (dict[str, Any] | None, optional):
            Specific area in the PDF to extract text from.
            Defaults to None (extract from the entire page).
            If provided, should be a dictionary with the following keys:

                - "f": First page to extract from
                - "l": Last page to extract from
                - "x":  x-coordinate of the top-left corner of the area to extract (in pixels)
                - "y":  y-coordinate of the top-left corner of the area to extract (in pixels)
                - "W": Width of the area to extract (in pixels)
                - "H": Height of the area to extract (in pixels)
                - "r": Specifies the resolution, in DPI.

    Returns:
        str: The extracted text.

    Raises:
        FileNotFoundError: If the specified PDF file is not found.
        OSError: If pdftotext fails to extract text.
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    import subprocess

    if shutil.which("pdftotext"):
        cmd = ["pdftotext", "-layout", "-q", "-enc", "UTF-8"]
        if area_details is not None:
            # An area was specified
            # Validate the required keys were provided
            assert "f" in area_details, "Area f details missing"
            assert "l" in area_details, "Area l details missing"
            assert "r" in area_details, "Area r details missing"
            assert "x" in area_details, "Area x details missing"
            assert "y" in area_details, "Area y details missing"
            assert "W" in area_details, "Area W details missing"
            assert "H" in area_details, "Area H details missing"
            # Convert all of the values to strings
            for key in area_details:
                area_details[key] = str(area_details[key])
            cmd += [
                "-f",
                area_details["f"],
                "-l",
                area_details["l"],
                "-r",
                area_details["r"],
                "-x",
                area_details["x"],
                "-y",
                area_details["y"],
                "-W",
                area_details["W"],
                "-H",
                area_details["H"],
            ]
        cmd += [path, "-"]
        # Run the extraction
        out, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
        return out.decode("utf-8")
    raise OSError(
        "pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/"
    )
