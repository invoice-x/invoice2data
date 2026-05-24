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
