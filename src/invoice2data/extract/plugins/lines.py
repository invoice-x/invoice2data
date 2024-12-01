"""Plugin to extract individual lines from an invoice.

This plugin has been replaced by the "lines" parser. All new templates
should use the parser instead. It's provided for backward compatibility
only.
"""

from collections import OrderedDict
from typing import Any
from typing import Dict

from .. import parsers


def extract(
    self: "OrderedDict[str, Any]", content: str, output: Dict[str, Any]
) -> None:
    """Extract individual lines from an invoice.

    This plugin has been replaced by the "lines" parser. All new templates
    should use the parser instead. It's provided for backward compatibility
    only.

    Args:
        self (OrderedDict[str, Any]): The current instance of the class.
        content (str): The text content to parse.
        output (Dict[str, Any]): A dictionary to store the extracted data.
    """
    lines_data = parsers.lines.parse(self, "lines", self["lines"], content)
    if lines_data is not None:
        output["lines"] = lines_data
