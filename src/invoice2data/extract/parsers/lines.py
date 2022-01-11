"""
Parser to extract individual lines from an invoice.

Initial work and maintenance by Holger Brunn @hbrunn
"""

import re
import logging

logger = logging.getLogger(__name__)

DEFAULT_OPTIONS = {"line_separator": r"\n"}


def parse(template, _settings, content):
    """Try to extract lines from the invoice"""

    # First apply default options.
    settings = DEFAULT_OPTIONS.copy()
    settings.update(_settings)

    # Validate settings
    assert "start" in settings, "Lines start regex missing"
    assert "end" in settings, "Lines end regex missing"
    assert "line" in settings, "Line regex missing"

    start = re.search(settings["start"], content)
    end = re.search(settings["end"], content)
    if not start or not end:
        logger.warning(f"No lines found. Start match: {start}. End match: {end}")
        return
    content = content[start.end() : end.start()]
    lines = []
    current_row = {}

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
            match = re.search(settings["first_line"], line)
            if match:
                # The line matches the first_line pattern so append current row to output
                # then assign a new current_row
                if current_row:
                    lines.append(current_row)
                current_row = {field: value.strip() if value else "" for field, value in match.groupdict().items()}
                # Flip first_line_found boolean as first_line has been found
                # This will allow last_line and line to be matched on below
                first_line_found = True
                continue
        # If the first_line has not yet been found, do not look for line or last_line
        if first_line_found is False:
            continue
        if "last_line" in settings:
            # last_line pattern provided, so check if the current line is that line
            match = re.search(settings["last_line"], line)
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
        match = re.search(settings["line"], line)
        if match:
            # This is one of the lines between first_line and last_line
            # Parse the data and add it to the current_row
            current_row = parse_current_row(match, current_row)
            continue
        logger.debug("ignoring *%s* because it doesn't match anything", line)
    if current_row:
        # All lines processed, so append whatever the final current_row was to output
        lines.append(current_row)

    types = settings.get("types", [])
    for row in lines:
        for name in row.keys():
            if name in types:
                row[name] = template.coerce_type(row[name], types[name])

    return lines


def parse_current_row(match, current_row):
    # Parse the current row data
    for field, value in match.groupdict().items():
        current_row[field] = "%s%s%s" % (
            current_row.get(field, ""),
            current_row.get(field, "") and "\n" or "",
            value.strip() if value else "",
        )
    return current_row
