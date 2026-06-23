"""Output modules and the shared output-destination helper."""

import contextlib
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from typing import TextIO


#: ``--output-name`` values that stream to a standard stream instead of a file.
#: ``/dev/stdout`` / ``/dev/stderr`` are treated as portable aliases for the
#: Python streams (so they also work on platforms without those device files).
_STDOUT_ALIASES = frozenset({"-", "/dev/stdout"})
_STDERR_ALIASES = frozenset({"/dev/stderr"})


@contextlib.contextmanager
def open_output(path: str, suffix: str, **open_kwargs: Any) -> Iterator[TextIO]:
    """Open the destination for a given ``--output-name``.

    Streams to stdout for ``-`` / ``/dev/stdout`` and stderr for ``/dev/stderr``;
    otherwise writes to ``path`` with ``suffix`` appended when missing.

    Args:
        path (str): The requested output name.
        suffix (str): File extension to ensure (e.g. ``.json``) for file paths.
        **open_kwargs (Any): Extra arguments forwarded to ``Path.open`` for files.

    Yields:
        TextIO: The writable text stream (a standard stream is not closed here).
    """
    if path in _STDOUT_ALIASES:
        yield sys.stdout
    elif path in _STDERR_ALIASES:
        yield sys.stderr
    else:
        filename = path if path.endswith(suffix) else path + suffix
        with Path(filename).open("w", **open_kwargs) as handle:
            yield handle
