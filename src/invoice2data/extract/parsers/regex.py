# SPDX-License-Identifier: MIT

"""
Parser extracting data using regexes.

One or more regexes can be specified using the "regex" setting.
By default it ignores duplicates and returns:
- single value if there was only a single match
- array for multiple matches

For more detailed parsing "type" and "group" settings can be specified.
"""

import re
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


def parse(template, settings, content, legacy=False):
    if "regex" not in settings:
        return None

    result = []
    if isinstance(settings["regex"], list):
        for regex in settings["regex"]:
            matches = re.findall(regex, content)
            if matches:
                result += matches
    else:
        result = re.findall(settings["regex"], content)

    if "type" in settings:
        for k, v in enumerate(result):
            result[k] = template.coerce_type(v, settings["type"])

    if "group" in settings:
        if settings["group"] == "sum":
            result = sum(result)
        else:
            logger.warning("Unsupported grouping method: " + settings["group"])
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
