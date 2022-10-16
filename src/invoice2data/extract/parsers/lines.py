"""
Parser to extract individual lines from an invoice.

Initial work and maintenance by Holger Brunn @hbrunn
"""

import re
import logging

logger = logging.getLogger(__name__)

DEFAULT_OPTIONS = {"line_separator": r"\n"}


def parse_line(patterns, line):
    patterns = patterns if isinstance(patterns, list) else [patterns]
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match
    return None


def parse_block(template, field, settings, content):
    # Validate settings
    assert "line" in settings, "Line regex missing"

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
            match = parse_line(settings["first_line"], line)
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
        # Just continue to the next line
        if first_line_found is False:
            continue
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
                skip_line_results = [re.search(x, line) for x in settings["skip_line"]]
            else:
                # Or a simple string
                skip_line_results = [re.search(settings["skip_line"], line)]
            if any(skip_line_results):
                # There was at least one match to a skip_line
                logger.debug("skip_line match on *%s*", line)
                continue
        # If none of those have continued the loop, check if this is just a normal line
        match = parse_line(settings["line"], line)
        if match:
            # This is one of the lines between first_line and last_line
            # Parse the data and add it to the current_row
            current_row = parse_current_row(match, current_row)
            continue
        # If the line doesn't match anything, log and continue to next line
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


def parse(template, field, _settings, content):
    # First apply default options.
    settings = DEFAULT_OPTIONS.copy()
    settings.update(_settings)

    # Validate settings
    assert "start" in settings, "Lines start regex missing"
    assert "end" in settings, "Lines end regex missing"

    blocks_count = 0
    lines = []

    # Try finding & parsing blocks of lines one by one
    while True:
        start = re.search(settings["start"], content)
        if not start:
            break
        content = content[start.end():]

        end = re.search(settings["end"], content)
        if not end:
            logger.warning("Failed to find lines block end")
            break

        blocks_count += 1
        lines += parse_block(template, field, settings, content[0:end.start()])

        content = content[end.end():]

    if blocks_count == 0:
        logger.warning("Failed to find any matching block (part) of invoice for \"%s\"", field)
    elif not lines:
        logger.warning("Failed to find any lines for \"%s\"", field)

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
