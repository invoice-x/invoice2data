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

    if isinstance(settings["regex"], list):
        regexes = settings["regex"]
    else:
        regexes = [settings["regex"]]

    result = []
    for regex in regexes:
        if not isinstance(regex, str):
            logger.warning('Field "%s" regex is not a string (%s)', field, str(regex))

            continue
        matches = re.findall(regex, content)
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

    if "type" in settings:
        for k, v in enumerate(result):
            result[k] = template.coerce_type(v, settings["type"])

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
    else:
        # Remove duplicates maintaining the order by default (it's more
        # natural). Don't do that for legacy parsing to keep backward
        # compatibility.
        if legacy:
            result = list(set(result))
        else:
            result = list(OrderedDict.fromkeys(result))

    if isinstance(result, list) and len(result) == 1:
        result = result[0]

    return result
