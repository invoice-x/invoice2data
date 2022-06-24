"""
Parser to extract individual lines from an invoice.

Initial work and maintenance by Holger Brunn @hbrunn
"""


import re
import logging

logger = logging.getLogger(__name__)

# Initialize the settings
# by setting the first_line_found boolean to False,
# This indicates the we are looking for the first_line pattern
DEFAULT_OPTIONS = {"line_separator": r"\n", "first_line_found": False}


def parse(template, field, _settings, content):
    """Try to extract lines from the invoice"""
    # logger.debug("_settings is *%s* for debugging", _settings)
    lines = []
    current_row = []
    plugin_settings = DEFAULT_OPTIONS.copy()
    indexno = -1

    # Backward Compatability if someone trys to pass something else instead of a list
    if type(_settings) != list:
        li = []
        li.append(_settings)
        _settings = li

    for setting in _settings:
        logger.debug(" Settingcheck: is \n *%s*", setting)
        # As first_line and last_line are optional, if neither were provided,
        # set the first_line to be the provided line parameter.
        # In this way the code will simply loop through and extract the lines as expected.

        if "first_line" not in setting and "last_line" not in setting:
            logger.debug("temp Setting : is \n *%s*", setting)
            setting["first_line"] = setting["line"]
            # this does not seem to work, but it should
            # Move this code outside of the line section

        # Set the setting number to act as an index for the current_row dict
        indexno += 1
        setting["index"] = indexno
        logger.debug("Setting %s: is \n *%s*", indexno, setting)
        current_row.append("")
        plugin_settings.update(setting)

        # First apply default options.
        plugin_settings.update(setting)
        setting = plugin_settings

        # Validate settings
        assert "start" in setting, "Lines start regex missing"
        assert "end" in setting, "Lines end regex missing"
        assert "line" in setting, "Line regex missing"

        start = re.search(setting["start"], content)
        end = re.search(setting["end"], content)
        if not start or not end:
            logger.warning(f"No lines found. Start match: {start}. End match: {end}")
            return

    for line_content in re.split(plugin_settings["line_separator"], content):

        # not sure if code below should stay.
        # match_emptyline = re.fullmatch("^\s+\n?\r?$",line_content) # .strip("^\s+$\n?\r?")
        # if match_emptyline:
        #    logger.debug(f"Empty line found, skipping")
        #    continue

        # If the line has empty lines in it , skip them
        if not line_content.strip("").strip("\n").strip("\r") or not line_content:
            continue
        # added .strip("^\s+$")
        logger.debug("Parsing line *%s*", line_content)
        # Loop trough settings from the template file.
        # As we want to have the output in the same order as the invoice file.
        for setting in _settings:

            if "first_line_found" not in setting:
                setting["first_line_found"] = False

            # Strip the content down to the items between start and end tag of this setting
            start = re.search(setting["start"], content)
            end = re.search(setting["end"], content)
            content_of_setting = content[start.end() : end.start()]

            # search if the current line is in the content.
            # If the current line is not between the start and end tag.
            # continue to the next setting in the for loop.
            content_is_between_start_end = re.search(re.escape(line_content), content_of_setting)
            if content_is_between_start_end:
                logger.debug("Setting %s: This line is between start and end tag", setting["index"])
            else:
                continue

            # We assume that structured line fields may either be individual lines or
            # they may be main line items with descriptions or details following beneath.
            # Using the first_line, line, last_line parameters we are able to capture this data.
            # first_line - The main line item
            # line - The detail lines
            # last_line - The final line
            # The code below will ignore both line and last_line until it finds first_line.
            # It will then switch to extracting line patterns until it either reaches last_line
            # or it reaches another first_line.

            # here loop trough settings
            if "first_line" in setting:
                # Check if the current lines the first_line pattern
                match = re.search(setting["first_line"], line_content)
                if match:
                    # The line matches the first_line pattern so append
                    logger.debug("Setting %s: first_line matched", setting["index"])
                    logger.debug("Setting %s: converting first_line to data:", setting["index"])
                    # on first_line always begin a new output line.
                    current_row[setting["index"]] = {}
                    current_row[setting["index"]] = parse_current_row(match, current_row[setting["index"]])
                    # Flip first_line_found boolean as first_line has been found
                    # This will allow last_line and line to be matched
                    setting["first_line_found"] = True
                    continue

            # If the first_line has not yet been found, do not look for line or last_line
            # Just continue to the next line
            if not setting['first_line_found']:
                logger.debug("Setting %s: Skipping because first_line is not found!", setting["index"])
                continue

            # Next we see if this is a line that should be skipped
            if "skip_line" in setting:
                # If skip_line was provided, check for a match now
                if isinstance(setting["skip_line"], list):
                    # Accepts a list
                    skip_line_results = [re.search(x, line_content) for x in setting["skip_line"]]
                else:
                    # Or a simple string
                    skip_line_results = [re.search(setting["skip_line"], line_content)]
                if any(skip_line_results):
                    # There was at least one match to a skip_line
                    logger.debug("skip_line match on *%s*", line_content)
                    continue

            # If last_line was provided, check that
            if "last_line" in setting:
                # last_line pattern provided, so check if the current line is that line
                match = re.search(setting["last_line"], line_content)
                if match:
                    # This is the last_line, so parse all lines thus far,
                    # append the values to the lines output.
                    # and reset current_row
                    logger.debug("Setting %s: converting last_line to data:", setting["index"])
                    current_row[setting["index"]] = parse_current_row(match, current_row[setting["index"]])
                    if current_row[setting["index"]]:
                        lines.append(current_row[setting["index"]])
                        logger.debug(
                            "Setting %s: last_line found, assembled result:\n *%s*",
                            setting["index"], current_row[setting["index"]]
                        )
                    current_row[setting["index"]] = {}
                    # Flip first_line_found boolean to look for first_line again on next loop
                    setting["first_line_found"] = False
                    continue

            # If none of those have continued the loop, check if this is just a normal line
            match = re.search(setting["line"], line_content)
            if match:
                # This is one of the lines between first_line and last_line
                # Parse the data and add it to the current_row
                logger.debug("Setting %s: converting line to data:", setting["index"])
                current_row[setting["index"]] = parse_current_row(match, current_row[setting["index"]])
                continue

            # All lines processed, so append whatever the final current_row was to output
            if current_row[setting["index"]]:
                lines.append(current_row[setting["index"]])
                logger.debug(
                    "Setting %s: all lines processed, result: %s", setting["index"],
                    current_row[setting["index"]]
                )
                current_row[setting["index"]] = {}
            # else:
                # If the line doesn't match anything, log and continue to next line
                # logger.debug("Setting %s: ignoring the line because it doesn't match anything", setting["index"])

    types = setting.get("types", [])
    for row in lines:
        for name in row.keys():
            if name in types:
                row[name] = template.coerce_type(row[name], types[name])
    return lines


def parse_current_row(match, current_row):
    # Parse the current row data
    # append the data to the key
    for field, value in match.groupdict().items():
        logger.debug("result: {'%s': '%s'} ", field, value)
        current_row[field] = "%s%s%s" % (
            current_row.get(field, ""),
            current_row.get(field, "") and "\n" or "",
            value.strip() if value else "",
        )
    return current_row
