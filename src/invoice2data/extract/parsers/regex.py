#!/usr/bin/python
# SPDX-License-Identifier: MIT

"""Parser extracting data using regexes.

One or more regexes can be specified using the "regex" setting.
By default it ignores duplicates and returns:
- single value if there was only a single match
- array for multiple matches

For more detailed parsing "type" and "group" settings can be specified.
"""

import logging
from collections import OrderedDict
from typing import Any

from .. import _regex
from ..utils import _apply_grouping


logger = logging.getLogger(__name__)


def parse(
    template: Any,
    field: str,
    settings: dict[str, Any],
    content: str,
    legacy: bool = False,
) -> Any:
    """Parse a field from the content using regular expressions.

    Args:
        template (Any): The template object.
        field (str): The name of the field to extract.
        settings (dict[str, Any]): The settings for the field extraction.
        content (str): The text content to parse.
        legacy (bool, optional): Whether to use legacy parsing. Defaults to False.

    Returns:
        Any: The extracted value(s) or None if parsing fails.
    """
    if "regex" not in settings:
        logger.warning('Field "%s" doesn\'t have regex specified', field)
        return None

    # `result` morphs from a list of matches to a coerced scalar/grouped value;
    # keep it `Any` so mypyc doesn't strict-check it against the initial list type.
    result: Any = _extract_matches(field, settings, content)
    if result is None:
        return None

    result = _apply_replace(settings, result)

    result = _apply_extract_number(settings, result)

    result = _apply_type_coercion(template, settings, result)

    result = _apply_grouping(settings, result)

    result = _remove_duplicates(legacy, result)

    if isinstance(result, list) and len(result) == 1:
        result = result[0]

    return result


def _extract_matches(
    field: str, settings: dict[str, Any], content: str
) -> list[Any] | None:
    """Extract matches from the content using the given regexes."""
    if isinstance(settings["regex"], list):
        regexes = settings["regex"]
    else:
        regexes = [settings["regex"]]

    result = []
    for regex in regexes:
        if not isinstance(regex, str):
            logger.warning(
                'Field "%s" regex is not a string (%s)',
                field,
                str(regex),
            )
            continue

        matches = _regex.findall(regex, content)
        logger.debug(
            "field=\033[1m\033[93m%s\033[0m | regex=\033[36m%s\033[0m | matches=\033[1m\033[92m%s\033[0m",
            field,
            settings["regex"],
            matches,
        )
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    logger.warning(
                        "Regex can't contain multiple capturing groups %s", regex
                    )
                    return None
            result += matches
    return result


def _normalize_replacements(spec: Any) -> list[tuple[str, str]]:
    r"""Normalize a field ``replace`` setting to a list of (pattern, repl) pairs.

    Accepts a single flat pair ``["\W+", ""]`` or a list of pairs
    ``[["\W+", ""], ["PS", "unit"]]``.
    """
    if len(spec) == 2 and all(isinstance(item, str) for item in spec):
        return [(spec[0], spec[1])]
    return [(pair[0], pair[1]) for pair in spec]


def _replace_value(value: Any, replacements: list[tuple[str, str]]) -> Any:
    """Apply each (pattern, repl) regex substitution to a single string value."""
    if not isinstance(value, str):
        return value
    for pattern, repl in replacements:
        value = _regex.sub(pattern, repl, value)
    return value


def _apply_replace(settings: dict[str, Any], result: list[Any]) -> list[Any]:
    r"""Apply a field-level ``replace`` to each matched value (issue #497).

    Lets a template use a simple regex and sanitize the captured value, e.g.
    ``replace: ["\W+", ""]`` turns ``NL.999,999.999,B01`` into ``NL999999999B01``.
    """
    if "replace" not in settings:
        return result
    replacements = _normalize_replacements(settings["replace"])
    return [_replace_value(value, replacements) for value in result]


#: First numeric token in a string -- sign + digits with optional thousands /
#: decimal separators (``.``, ``,``, whitespace, ``'``). Does NOT truncate
#: large numbers: matches ``1234``, ``1234.56``, ``1.234,56``, ``1,234.56``,
#: ``12123``, ``25.50``, ``-42`` in full. Locale-aware splitting into integer
#: vs decimal is left to :func:`InvoiceTemplate.parse_number` downstream.
_NUMBER_RE = r"[-+]?\d+(?:[.,\s']\d+)*"


def _extract_number(value: Any) -> Any:
    """Pluck the first numeric token from a string that may contain units/text.

    Returns the input unchanged if it isn't a string or contains no digits, so
    later steps (replace, type coercion) see the same value they would have
    seen without ``extract_number: true``.

    Args:
        value (Any): A single captured value from the regex parser.

    Returns:
        Any: The matched numeric substring, or the original value on miss.
    """
    if not isinstance(value, str):
        return value
    match = _regex.search(_NUMBER_RE, value)
    return match.group() if match else value


def _apply_extract_number(settings: dict[str, Any], result: list[Any]) -> list[Any]:
    """Extract the first numeric token from each captured value, when opted in.

    Enabled per-field with ``extract_number: true``. Useful when the regex
    captures a wider region than the number itself (e.g. ``"12123 Stk."`` ->
    ``"12123"``, ``"€25.50"`` -> ``"25.50"``). Runs *after* ``replace`` and
    *before* type coercion so ``parse_number`` sees a clean numeric string.

    Args:
        settings (dict[str, Any]): The field's configuration.
        result (list[Any]): The list of captured values to process.

    Returns:
        list[Any]: The list with numeric tokens extracted (unchanged if the
            field does not opt in).
    """
    if not settings.get("extract_number"):
        return result
    return [_extract_number(value) for value in result]


def _apply_type_coercion(
    template: Any, settings: dict[str, Any], result: list[Any]
) -> list[Any]:
    """Apply type coercion to the extracted values."""
    if "type" in settings:
        for k, v in enumerate(result):
            result[k] = template.coerce_type(v, settings["type"])
    return result


def _remove_duplicates(legacy: bool, result: Any | None) -> Any | None:
    """Remove duplicate values from the result."""
    if isinstance(result, list):
        result = list(set(result)) if legacy else list(OrderedDict.fromkeys(result))
    return result
