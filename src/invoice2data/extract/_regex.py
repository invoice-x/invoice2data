"""Internal regex helpers with a compile-once cache.

All regex matching in :mod:`invoice2data.extract` goes through these thin
wrappers so each pattern is compiled only once (via an LRU cache) instead of on
every call. The engine is selected once at import time: the stdlib :mod:`re` by
default, or the API-compatible third-party ``regex`` package when
``INVOICE2DATA_REGEX_ENGINE=regex`` is set in the environment.
"""

import os
import re
from functools import lru_cache
from typing import Any
from typing import cast


_engine: Any = re
if os.environ.get("INVOICE2DATA_REGEX_ENGINE", "re").lower() == "regex":
    try:
        import regex  # type: ignore[import-untyped]

        _engine = regex
    except ImportError:  # pragma: no cover
        pass

#: Name of the active regex engine ("re" or "regex").
ENGINE: str = _engine.__name__


@lru_cache(maxsize=4096)
def compile(pattern: str, flags: int = 0) -> "re.Pattern[str]":
    """Compile a regex pattern, caching the result.

    Args:
        pattern (str): The regular expression pattern.
        flags (int): Regex flags passed to the engine. Defaults to 0.

    Returns:
        re.Pattern[str]: The compiled pattern object. The active engine
            (`re` or the API-compatible `regex`) is treated as `re` for typing.
    """
    return cast("re.Pattern[str]", _engine.compile(pattern, flags))


def search(pattern: str, string: str, flags: int = 0) -> "re.Match[str] | None":
    """Search ``string`` for the first match of ``pattern``.

    Args:
        pattern (str): The regular expression pattern.
        string (str): The text to search.
        flags (int): Regex flags. Defaults to 0.

    Returns:
        re.Match[str] | None: A match object, or None if there is no match.
    """
    return compile(pattern, flags).search(string)


def findall(pattern: str, string: str, flags: int = 0) -> Any:
    """Return all non-overlapping matches of ``pattern`` in ``string``.

    Args:
        pattern (str): The regular expression pattern.
        string (str): The text to search.
        flags (int): Regex flags. Defaults to 0.

    Returns:
        Any: A list of matches (strings or tuples of groups).
    """
    return compile(pattern, flags).findall(string)


def finditer(pattern: str, string: str, flags: int = 0) -> Any:
    """Iterate over all non-overlapping match objects of ``pattern`` in ``string``.

    Args:
        pattern (str): The regular expression pattern.
        string (str): The text to search.
        flags (int): Regex flags. Defaults to 0.

    Returns:
        Any: A callable iterator yielding ``re.Match`` objects (or the active
            engine's equivalent).
    """
    return compile(pattern, flags).finditer(string)


def split(pattern: str, string: str, maxsplit: int = 0, flags: int = 0) -> Any:
    """Split ``string`` by occurrences of ``pattern``.

    Args:
        pattern (str): The regular expression pattern.
        string (str): The text to split.
        maxsplit (int): Maximum number of splits. Defaults to 0 (no limit).
        flags (int): Regex flags. Defaults to 0.

    Returns:
        Any: A list of substrings.
    """
    return compile(pattern, flags).split(string, maxsplit)


def sub(pattern: str, repl: str, string: str, count: int = 0, flags: int = 0) -> str:
    """Replace occurrences of ``pattern`` in ``string`` with ``repl``.

    Args:
        pattern (str): The regular expression pattern.
        repl (str): The replacement string.
        string (str): The text to operate on.
        count (int): Maximum number of replacements. Defaults to 0 (all).
        flags (int): Regex flags. Defaults to 0.

    Returns:
        str: The string with replacements applied.
    """
    return compile(pattern, flags).sub(repl, string, count)
