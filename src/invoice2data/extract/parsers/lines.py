"""Parser to extract individual lines from an invoice.

Initial work and maintenance by Holger Brunn @hbrunn
"""

import re
from logging import getLogger
from typing import Any
from typing import Dict
from typing import List
from typing import Match
from typing import Optional
from typing import Union


# from ..invoice_template import InvoiceTemplate  # type: ignore[unused-ignore]

logger = getLogger(__name__)

DEFAULT_OPTIONS = {"line_separator": r"\n"}


def parse_line(patterns: Union[str, List[str]], line: str) -> Optional[Match[str]]:
    """Parse a line using a given pattern or list of patterns.

    This function searches for a match in the given line using the provided
    pattern or list of patterns. If a match is found, it returns the match
    object; otherwise, it returns None.

    Args:
        patterns (Union[str, List[str]]): The pattern(s) to search for.
        line (str): The line to parse.

    Returns:
        Optional[Match[str]]: A match object if a match is found, otherwise None.
    """
    patterns = patterns if isinstance(patterns, list) else [patterns]
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match
    return None


def parse_block(  # noqa: RUF100 C901
    template: Dict[str, Any],
    field: str,
    settings: Dict[str, Any],
    content: str,
) -> List[Dict[str, Any]]:
    """Parse a block of lines to extract data.

    This function parses a block of lines from an invoice to extract data
    based on the provided template and settings. It handles different line
    types (first line, last line, regular lines) and can skip specific lines
    based on the configuration.

    Args:
        template (Dict[str, Any]): The template containing extraction rules.
        field (str): The name of the field to extract.
        settings (Dict[str, Any]): The settings for the extraction rule.
        content (str): The text content to parse.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                represents an extracted row with field-value pairs.
    """
    # Validate settings
    assert "line" in settings, (
        "Error in Template %s Line regex missing" % template["template_name"]
    )

    logger.debug("START lines block content ========================\n%s", content)
    logger.debug("END lines block content ==========================")
    lines: List[Dict[str, Any]] = []
    current_row: Dict[str, Any] = {}

    # We assume that structured line fields may either be individual lines or
    # they may be main line items with descriptions or details following beneath.
    # Using the first_line, line, last_line parameters we are able to capture this data.
    # first_line - The main line item
    # line - The detail lines, typically indented from the main lines
    # last_line - The final line of the indented lines
    # The code below will ignore both line and last_line until it finds first_line.
    # It will then switch to extracting line patterns until it either reaches last_line
    # or it reaches another first_line.

    # As first_line and last_line are optional, if neither were provided,
    # set the first_line to be the provided line parameter.
    # In this way the code will simply loop through and extract the lines as expected.
    if "first_line" not in settings and "last_line" not in settings:
        settings["first_line"] = settings["line"]
    # As we enter the loop, we set the boolean for first_line being found to False,
    # This indicates the we are looking for the first_line pattern
    first_line_found = False
    for line in re.split(settings["line_separator"], content):
        # If the line has empty lines in it , skip them
        if not line.strip("").strip("\n").strip("\r") or not line:
            continue
        if "first_line" in settings:
            # Check if the current lines the first_line pattern
            match = parse_line(settings["first_line"], line)
            if match:
                # The line matches the first_line pattern so append current row to output
                # then assign a new current_row
                if current_row:
                    lines.append(current_row)
                current_row = {
                    field: value.strip() if value else ""
                    for field, value in match.groupdict().items()
                }
                # Flip first_line_found boolean as first_line has been found
                # This will allow last_line and line to be matched on below
                first_line_found = True
                continue
        # Look for line or last_line only if the first has has been found
        if first_line_found is True:
            # If last_line was provided, check that
            if "last_line" in settings:
                # last_line pattern provided, so check if the current line is that line
                match = parse_line(settings["last_line"], line)
                if match:
                    # This is the last_line, so parse all lines thus far,
                    # append to output,
                    # and reset current_row
                    current_row = parse_current_row(match, current_row)
                    if current_row:
                        lines.append(current_row)
                    current_row = {}
                    # Flip first_line_found boolean to look for first_line again on next loop
                    first_line_found = False
                    continue
            # Next we see if this is a line that should be skipped
            if "skip_line" in settings:
                # If skip_line was provided, check for a match now
                if isinstance(settings["skip_line"], list):
                    # Accepts a list
                    skip_line_results = [
                        re.search(x, line) for x in settings["skip_line"]
                    ]
                else:
                    # Or a simple string
                    skip_line_results = [re.search(settings["skip_line"], line)]
                if any(skip_line_results):
                    # There was at least one match to a skip_line
                    logger.debug("skip_line match on \ns*%s*", line)
                    continue
            # If none of those have continued the loop, check if this is just a normal line
            match = parse_line(settings["line"], line)
            if match:
                # This is one of the lines between first_line and last_line
                # Parse the data and add it to the current_row
                current_row = parse_current_row(match, current_row)
                continue
        # If the line doesn't match anything, log and continue to next line
        logger.debug("The following line doesn't match anything:\n*%s*", line)
    if current_row:
        # All lines processed, so append whatever the final current_row was to output
        lines.append(current_row)

    types = settings.get("types", [])
    for row in lines:
        for name in row.keys():
            if name in types:
                row[name] = template.coerce_type(row[name], types[name])  # type: ignore[attr-defined]
    return lines


def parse_by_rule(
    template: Dict[str, Any],
    field: str,
    rule: Dict[str, Any],
    content: str,
) -> List[Dict[str, Any]]:
    """Parse lines from a block of text based on a rule.

    Args:
        template (Dict[str, Any]): The template dictionary.
        field (str): The field name.
        rule (Dict[str, Any]): The rule dictionary.
        content (str): The text content to parse.

    Returns:
        List[Dict[str, Any]]: The parsed lines.
    """
    # First apply default options.
    settings = DEFAULT_OPTIONS.copy()
    settings.update(rule)

    # Validate settings
    assert "start" in settings, (
        "Error in Template %s Lines start regex missing" % template["template_name"]
    )
    assert "end" in settings, (
        "Error in Template %s Lines end regex missing" % template["template_name"]
    )

    blocks_count = 0
    lines = []

    # Try finding & parsing blocks of lines one by one
    while True:
        start = re.search(settings["start"], content)
        if not start:
            logger.debug("Failed to find lines block start")
            break
        content = content[start.end() :]

        end = re.search(settings["end"], content)
        if not end:
            logger.debug("Failed to find lines block end")
            break

        blocks_count += 1
        lines += parse_block(template, field, settings, content[0 : end.start()])

        content = content[end.end() :]

    if blocks_count == 0:
        logger.warning(
            'Failed to find any matching block (part) of invoice for "%s"', field
        )
    elif not lines:
        logger.warning('Failed to find any lines for "%s"', field)

    return lines


def parse(
    template: Dict[str, Any],
    field: str,
    settings: Dict[str, Any],
    content: str,
) -> List[Dict[str, Any]]:
    """Parse lines from the content based on the given settings.

    Args:
        template (Dict[str, Any]): The template dictionary.
        field (str): The field name.
        settings (Dict[str, Any]): The settings dictionary.
        content (str): The text content to parse.

    Returns:
        List[Dict[str, Any]]: The parsed lines.
    """
    if "rules" in settings:
        # One field can have multiple sets of line-parsing rules
        rules = settings["rules"]
    else:
        # Original syntax stored line-parsing rules in top field YAML object
        keys = ("start", "end", "line", "first_line", "last_line", "skip_line", "types")
        rules = [{k: v for k, v in settings.items() if k in keys}]

    lines = []
    for i, rule in enumerate(rules):
        logger.debug("Testing Rules set #%s", i)
        new_lines = parse_by_rule(template, field, rule, content)
        if new_lines is not None:
            lines += new_lines

    return lines


def parse_current_row(
    match: Optional[Match[str]], current_row: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse the current row data.

    Args:
        match (Optional[Match[str]]): The match object.
        current_row (Dict[str, Any]): The current row dictionary.

    Returns:
        Dict[str, Any]: The updated current row dictionary.
    """
    if match:
        for field, value in match.groupdict().items():
            current_row[field] = "%s%s%s" % (
                current_row.get(field, ""),
                (current_row.get(field, "") and "\n") or "",
                value.strip() if value else "",
            )
    return current_row
