"""Plugin to extract tables from an invoice."""

import re
from collections import OrderedDict
from logging import getLogger
from typing import Any
from typing import Dict
from typing import Optional


logger = getLogger(__name__)

DEFAULT_OPTIONS = {"field_separator": r"\s+", "line_separator": r"\n"}


def extract(
    self: "OrderedDict[str, Any]", content: str, output: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Try to extract tables from an invoice.

    Args:
        self (InvoiceTemplate): The current instance of the class.  # noqa: DOC103
        content (str): The content of the invoice.
        output (Dict[str, Any]): A dictionary to store the extracted data.

    Returns:
        Optional[Dict[str, Any]]: The updated output dictionary with extracted
                                   data, or None if date parsing fails.
    """
    for i, table in enumerate(self["tables"]):
        logger.debug("Testing Rules set #%s", i)

        # Extract and validate settings
        table = _extract_and_validate_settings(self, table)
        if table is None:
            continue

        # Extract table body
        table_body = _extract_table_body(content, table)
        if table_body is None:
            continue

        # Process table lines
        if not _process_table_lines(self, table, table_body, output):
            return None  # Return None if date parsing fails

    return output


def _extract_and_validate_settings(
    self: "OrderedDict[str, Any]",
    table: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Extract and validate table settings.

    Args:
        self (InvoiceTemplate): The current instance of the class.  # noqa: DOC103
        table (Dict[str, Any]): A dictionary containing the table settings.

    Returns:
        Optional[Dict[str, Any]]: The validated table settings, or None if
                                   validation fails.
    """
    plugin_settings = DEFAULT_OPTIONS.copy()
    plugin_settings.update(table)
    table = plugin_settings

    for key in ("start", "end", "body"):
        assert (
            key in table
        ), f"Error in Template {self['template_name']} Table {key} regex missing"
    return table


def _extract_table_body(content: str, table: Dict[str, Any]) -> Optional[str]:
    """Extract the table body from the content.

    Args:
        content (str): The content of the invoice.
        table (Dict[str, Any]): The validated table settings.

    Returns:
        Optional[str]: The extracted table body, or None if start or end
                       regexes are not found.
    """
    start = re.search(table["start"], content)
    end = re.search(table["end"], content)

    if not start:
        logger.debug("Failed to find the start of the table")
        return None

    if not end:
        logger.debug("Failed to find the end of the table")
        return None

    table_body = content[start.end() : end.start()]
    logger.debug("START table body content ========================\n%s", table_body)
    logger.debug("END table body content ==========================")
    return table_body


def _process_table_lines(
    self: "OrderedDict[str, Any]",
    table: Dict[str, Any],
    table_body: str,
    output: Dict[str, Any],
) -> bool:
    """Process the lines within the table body.

    Args:
        self (InvoiceTemplate): The current instance of the class.  # noqa: DOC103
        table (Dict[str, Any]): The validated table settings.
        table_body (str): The extracted table body.
        output (Dict[str, Any]): A dictionary to store the extracted data.

    Returns:
        bool: True if processing is successful, False if date parsing fails.
    """
    types = table.get("types", {})
    no_match_found = True

    for line in re.split(table["line_separator"], table_body):
        if not line.strip("").strip("\n") or line.isspace():
            continue

        # Correct the function call and return logic
        if not _process_table_line(self, table, line, types, output):
            return False  # Return False immediately if date parsing fails
        else:
            no_match_found = (
                False  # Update no_match_found only if line processing is successful
            )

    if no_match_found:
        logger.debug(
            "\033[1;43mWarning\033[0m regex=\033[91m*%s*\033[0m doesn't match anything!",
            table["body"],
        )
    return True


def _process_table_line(
    self: "OrderedDict[str, Any]",
    table: Dict[str, Any],
    line: str,
    types: Dict[str, Any],
    output: Dict[str, Any],
) -> bool:
    """Process a single line within the table body.

    Args:
        self (InvoiceTemplate): The current instance of the class.
        table (Dict[str, Any]): The validated table settings.
        line (str): A single line from the table body.
        types (Dict[str, Any]): A dictionary of type coercion rules.
        output (Dict[str, Any]): A dictionary to store the extracted data.

    Returns:
        bool: True if processing is successful, False if date parsing fails.
    """
    match = re.search(table["body"], line)
    if match:
        for field, value in match.groupdict().items():
            if field in output:
                continue

            logger.debug(
                (
                    "field=\033[1m\033[93m%s\033[0m |"
                    "regex=\033[36m%s\033[0m | "
                    "matches=\033[1m\033[92m['%s']\033[0m"
                ),
                field,
                match.re.pattern,
                value,
            )

            if field.startswith("date") or field.endswith("date"):
                output[field] = self.parse_date(value)  # type: ignore[attr-defined]
                if not output[field]:
                    logger.error("Date parsing failed on date *%s*", value)
                    return False
            elif field.startswith("amount"):
                output[field] = self.parse_number(value)  # type: ignore[attr-defined]
            elif field in types:
                # Access types as a dictionary
                output[field] = self.coerce_type(value, types[field])  # type: ignore[attr-defined]
            else:
                output[field] = value

        # Return True if a match is found and processed successfully
        return True
    else:
        logger.debug("The following line doesn't match anything:\n*%s*", line)
        # Return True to continue processing even if a line doesn't match
        return True
