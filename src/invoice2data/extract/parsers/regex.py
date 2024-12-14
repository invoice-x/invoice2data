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
import re
from collections import OrderedDict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


logger = logging.getLogger(__name__)


def parse(
    template: Any,
    field: str,
    settings: Dict[str, Any],
    content: str,
    legacy: bool = False,
) -> Any:
    """Parse a field from the content using regular expressions.

    Args:
        template (Any): The template object.
        field (str): The name of the field to extract.
        settings (Dict[str, Any]): The settings for the field extraction.
        content (str): The text content to parse.
        legacy (bool, optional): Whether to use legacy parsing. Defaults to False.

    Returns:
        Any: The extracted value(s) or None if parsing fails.
    """
    if "regex" not in settings:
        logger.warning('Field "%s" doesn\'t have regex specified', field)
        return None

    result = _extract_matches(settings, content)
    if result is None:
        return None

    result = _apply_type_coercion(template, settings, result)

    result = _apply_grouping(settings, result)

    result = _remove_duplicates(legacy, result)

    if isinstance(result, list) and len(result) == 1:
        result = result[0]

    return result


def _extract_matches(settings: Dict[str, Any], content: str) -> Optional[List[Any]]:
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
                settings.get("field", ""),
                str(regex),
            )
            continue

        matches = re.findall(regex, content)
        logger.debug(
            "field=\033[1m\033[93m%s\033[0m | regex=\033[36m%s\033[0m | matches=\033[1m\033[92m%s\033[0m",
            settings.get("field", ""),
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
    template: Any, settings: Dict[str, Any], result: List[Any]
) -> List[Any]:
    """Apply type coercion to the extracted values."""
    if "type" in settings:
        for k, v in enumerate(result):
            result[k] = template.coerce_type(v, settings["type"])
    return result


def _apply_grouping(settings: Dict[str, Any], result: Any) -> Optional[Any]:
    """Apply grouping to the extracted values."""
    if "group" in settings:
        result = list(filter(None, result))
        if result:
            if settings["group"] == "sum":
                result = sum(result)
            elif settings["group"] == "min":
                result = min(result)
            elif settings["group"] == "max":
                result = max(result)
            elif settings["group"] == "first":
                result = result[0]
            elif settings["group"] == "last":
                result = result[-1]
            elif settings["group"] == "join":
                joined = " ".join(str(v) for v in result) if result else ""
                result = [joined]
            else:
                logger.warning("Unsupported grouping method: %s", settings["group"])
                return None
    return result


def _remove_duplicates(legacy: bool, result: Optional[Any]) -> Optional[Any]:
    """Remove duplicate values from the result."""
    if isinstance(result, list):
        if legacy:
            result = list(set(result))
        else:
            result = list(OrderedDict.fromkeys(result))
    return result
