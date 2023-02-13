# SPDX-License-Identifier: MIT

"""
Pseudo-parser returning a static (predefined) value
"""

from logging import getLogger

logger = getLogger(__name__)


def parse(template, field, settings, content):
    if "value" not in settings:
        logger.warning("Field \"%s\" doesn't have static value specified", field)
        return None

    logger.debug("field=%s | value=['%s']", field, settings["value"])

    return settings["value"]
