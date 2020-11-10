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
        logger.warning("no lines found - start %s, end %s", start, end)
        return
    content = content[start.end() : end.start()]
    lines = []
    current_row = {}
    if "first_line" not in settings and "last_line" not in settings:
        settings["first_line"] = settings["line"]
    for line in re.split(settings["line_separator"], content):
        # if the line has empty lines in it , skip them
        if not line.strip("").strip("\n") or not line:
            continue
        if "first_line" in settings:
            match = re.search(settings["first_line"], line)
            if match:
                if "last_line" not in settings:
                    if current_row:
                        lines.append(current_row)
                    current_row = {}
                if current_row:
                    lines.append(current_row)
                current_row = {
                    field: value.strip() if value else ""
                    for field, value in match.groupdict().items()
                }
                continue
        if "last_line" in settings:
            match = re.search(settings["last_line"], line)
            if match:
                for field, value in match.groupdict().items():
                    current_row[field] = "%s%s%s" % (
                        current_row.get(field, ""),
                        current_row.get(field, "") and "\n" or "",
                        value.strip() if value else "",
                    )
                if current_row:
                    lines.append(current_row)
                current_row = {}
                continue
        match = re.search(settings["line"], line)
        if match:
            for field, value in match.groupdict().items():
                current_row[field] = "%s%s%s" % (
                    current_row.get(field, ""),
                    current_row.get(field, "") and "\n" or "",
                    value.strip() if value else "",
                )
            continue
        logger.debug("ignoring *%s* because it doesn't match anything", line)
    if current_row:
        lines.append(current_row)

    types = settings.get("types", [])
    for row in lines:
        for name in row.keys():
            if name in types:
                row[name] = template.coerce_type(row[name], types[name])

    return lines
