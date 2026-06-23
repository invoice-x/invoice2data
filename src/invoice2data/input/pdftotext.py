"""Poppler pdftotext input module for invoice2data.

Full-page extraction shells out to ``pdftotext -layout``. Area (region) extraction
no longer re-runs ``pdftotext`` per area: word positions are read once via
``pdftotext -bbox-layout`` (cached per file) and the requested rectangle is cropped
in Python, so several area fields on one document cost a single parse.
"""

import html
import re
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any


SUPPORTS_AREA = True

#: A parsed word: ``(page, xMin, yMin, xMax, yMax, text)`` with coords in points.
_Word = tuple[int, float, float, float, float, str]

#: Tokenizer for ``pdftotext -bbox-layout`` output: page boundaries + words with
#: their bounding boxes (in PDF points).
_BBOX_TOKEN = re.compile(
    r"<page\b"
    r'|<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
    re.DOTALL,
)

#: Words within this many points of each other's top are treated as one line.
_LINE_TOLERANCE = 3.0


def is_available() -> bool:
    """Return whether the poppler ``pdftotext`` binary is on the PATH.

    Returns:
        bool: True if ``pdftotext`` can be run.
    """
    return shutil.which("pdftotext") is not None


def _mtime(path: str) -> float:
    """Return the file's mtime (cache key), or 0.0 if it cannot be read.

    Args:
        path (str): File path.

    Returns:
        float: Modification time, or 0.0.
    """
    try:
        return Path(path).stat().st_mtime
    except OSError:
        return 0.0


@lru_cache(maxsize=64)
def _words(path: str, mtime: float) -> tuple[_Word, ...]:
    """Parse word positions from ``pdftotext -bbox-layout`` once, cached per file.

    Args:
        path (str): PDF path.
        mtime (float): File mtime, part of the cache key so edits re-parse.

    Returns:
        tuple[_Word, ...]: One word box per word, in points.
    """
    import subprocess

    cmd = ["pdftotext", "-bbox-layout", "-q", path, "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    words: list[_Word] = []
    page = 0
    for match in _BBOX_TOKEN.finditer(proc.stdout):
        if match.group(1) is None:  # a <page> token
            page += 1
            continue
        x_min, y_min, x_max, y_max, text = match.groups()
        words.append(
            (
                page,
                float(x_min),
                float(y_min),
                float(x_max),
                float(y_max),
                html.unescape(text),
            )
        )
    return tuple(words)


def _crop(words: tuple[_Word, ...], area: dict[str, Any]) -> str:
    """Return the text of the words inside an area rectangle.

    The area is given in pixels at ``r`` dpi (pdftotext's convention); word boxes
    are in points, so the rectangle is converted ``pt = px * 72 / r``. Selected
    words are grouped into lines by vertical position and joined left-to-right.

    Args:
        words (tuple[_Word, ...]): Word boxes from :func:`_words`.
        area (dict[str, Any]): Keys f, l, r, x, y, W, H.

    Returns:
        str: The cropped region's text (one line per detected line).
    """
    first, last = int(area["f"]), int(area["l"])
    factor = 72.0 / float(area["r"])
    x0 = float(area["x"]) * factor
    y0 = float(area["y"]) * factor
    x1 = (float(area["x"]) + float(area["W"])) * factor
    y1 = (float(area["y"]) + float(area["H"])) * factor

    selected = [
        w
        for w in words
        if first <= w[0] <= last and w[1] < x1 and w[3] > x0 and w[2] < y1 and w[4] > y0
    ]
    selected.sort(key=lambda w: (w[0], w[2], w[1]))

    lines: list[list[_Word]] = []
    current: list[_Word] = []
    last_y: float | None = None
    last_page: int | None = None
    for word in selected:
        if (
            last_y is not None
            and word[0] == last_page
            and abs(word[2] - last_y) <= _LINE_TOLERANCE
        ):
            current.append(word)
        else:
            if current:
                lines.append(current)
            current = [word]
        last_y, last_page = word[2], word[0]
    if current:
        lines.append(current)

    return "\n".join(
        " ".join(w[5] for w in sorted(line, key=lambda w: w[1])) for line in lines
    )


def to_text(path: str, area_details: dict[str, Any] | None = None) -> str:
    """Extract text from a PDF file using pdftotext.

    Args:
        path (str): Path to the PDF file.
        area_details (dict[str, Any] | None, optional): Restrict extraction to a
            region. Keys (pixels at ``r`` dpi): ``f``/``l`` (first/last page),
            ``x``/``y`` (top-left), ``W``/``H`` (size), ``r`` (resolution dpi).
            Defaults to None (whole document).

    Returns:
        str: The extracted text.

    Raises:
        FileNotFoundError: If the specified PDF file is not found.
        OSError: If pdftotext is not installed.
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not shutil.which("pdftotext"):
        raise OSError(
            "pdftotext not installed. "
            "Can be downloaded from https://poppler.freedesktop.org/"
        )

    if area_details is not None:
        for key in ("f", "l", "r", "x", "y", "W", "H"):
            assert key in area_details, f"Area {key} details missing"
        # Crop from the cached word positions -- one parse per file regardless of
        # how many area fields a template defines.
        return _crop(_words(path, _mtime(path)), area_details)

    import subprocess

    cmd = ["pdftotext", "-layout", "-q", "-enc", "UTF-8", path, "-"]
    out, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    return out.decode("utf-8")
