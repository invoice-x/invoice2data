"""This module abstracts utilities for processing of the extracted values."""

from logging import getLogger
from typing import Any
from typing import Dict
from typing import Optional


logger = getLogger(__name__)


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
