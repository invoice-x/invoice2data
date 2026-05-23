"""Plugin to extract individual lines from an invoice.

This plugin has been replaced by the "lines" parser. All new templates
should use the parser instead. It's provided for backward compatibility
only.
"""

import warnings
from typing import TYPE_CHECKING
from typing import Any

from .. import parsers


if TYPE_CHECKING:
    from ..invoice_template import InvoiceTemplate


def extract(
    self: "InvoiceTemplate",
    content: str,
    output: dict[str, Any],
    invoice_file: str | None = None,
) -> None:
    """Extract individual lines from an invoice.

    This plugin has been replaced by the "lines" parser. All new templates
    should use the parser instead. It's provided for backward compatibility
    only.

    Args:
        self (InvoiceTemplate): The current instance of the class.
        content (str): The text content to parse.
        output (dict[str, Any]): A dictionary to store the extracted data.
        invoice_file (str | None): Unused; accepted for plugin-interface
            compatibility (path-based plugins such as camelot need it).
    """
    warnings.warn(
        "The 'lines' plugin (a top-level 'lines:' template key) is deprecated "
        "and will be removed in a future release. Define it as a field with "
        "'parser: lines' instead. See docs/migration-1.0.md.",
        DeprecationWarning,
        stacklevel=2,
    )
    lines_data = parsers.lines.parse(self, "lines", self["lines"], content)
    if lines_data is not None:
        output["lines"] = lines_data
