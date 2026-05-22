# SPDX-License-Identifier: MIT

"""Pseudo-parser returning a static (predefined) value."""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)


def parse(
    template: Any,
    field: str,
    settings: dict[str, Any],
    content: str,
    legacy: bool = False,
) -> Any | None:
    if "value" not in settings:
        logger.warning('Field "%s" doesn\'t have static value specified', field)
        return None

    logger.debug("field=%s | value=['%s']", field, settings["value"])

    return settings["value"]
