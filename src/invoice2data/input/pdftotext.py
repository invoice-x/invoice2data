"""Poppler pdftotext input module for invoice2data."""

import os
from typing import Any
from typing import Dict
from typing import Optional


def to_text(path: str, area_details: Optional[Dict[str, Any]] = None) -> str:
    """Extract text from a PDF file using pdftotext.

    Args:
        path (str): Path to the PDF file.
        area_details (Optional[Dict[str, Any]], optional):
            Specific area in the PDF to extract text from.
            Defaults to None (extract from the entire page).

    Returns:
        str: The extracted text.

    Raises:
        FileNotFoundError: If the specified PDF file is not found.
        OSError: If pdftotext fails to extract text.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    import shutil
    import subprocess

    if shutil.which("pdftotext"):
        cmd = ["pdftotext", "-layout", "-q", "-enc", "UTF-8"]
        if area_details is not None:
            # An area was specified
            # Validate the required keys were provided
            assert "f" in area_details, "Area r details missing"
            assert "l" in area_details, "Area r details missing"
            assert "r" in area_details, "Area r details missing"
            assert "x" in area_details, "Area x details missing"
            assert "y" in area_details, "Area y details missing"
            assert "W" in area_details, "Area W details missing"
            assert "H" in area_details, "Area H details missing"
            # Convert all of the values to strings
            for key in area_details.keys():
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
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
        return out.decode("utf-8")
    else:
        raise OSError(
            "pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/"
        )
