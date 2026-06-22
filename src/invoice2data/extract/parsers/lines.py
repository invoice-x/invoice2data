"""Parser to extract individual lines from an invoice.

Initial work and maintenance by Holger Brunn @hbrunn
"""

from logging import getLogger
from re import Match
from typing import TYPE_CHECKING
from typing import Any

from .. import _regex
from .regex import _normalize_replacements
from .regex import _replace_value


if TYPE_CHECKING:
    from ..invoice_template import InvoiceTemplate


logger = getLogger(__name__)

DEFAULT_OPTIONS = {"line_separator": r"\n"}


def parse_line(patterns: str | list[str], line: str) -> Match[str] | None:
    """Parse a line using a given pattern or list of patterns.

    This function searches for a match in the given line using the provided
    pattern or list of patterns. If a match is found, it returns the match
    object; otherwise, it returns None.

    Args:
        patterns (str | list[str]): The pattern(s) to search for.
        line (str): The line to parse.

    Returns:
        Match[str] | None: A match object if a match is found, otherwise None.
    """
    patterns = patterns if isinstance(patterns, list) else [patterns]
    for pattern in patterns:
        match = _regex.search(pattern, line)
        if match:
            return match
    return None


def parse_block(  # noqa: RUF100 C901
    template: "InvoiceTemplate",
    field: str,
    settings: dict[str, Any],
    content: str,
) -> list[dict[str, Any]]:
    """Parse a block of lines to extract data.

    This function parses a block of lines from an invoice to extract data
    based on the provided template and settings. It handles different line
    types (first line, last line, regular lines) and can skip specific lines
    based on the configuration.

    Args:
        template (InvoiceTemplate): The template containing extraction rules.
        field (str): The name of the field to extract.
        settings (dict[str, Any]): The settings for the extraction rule.
        content (str): The text content to parse.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, where each dictionary
                                represents an extracted row with field-value pairs.
    """
    # Validate settings
    assert "line" in settings, (
        "Error in Template %s Line regex missing" % template["template_name"]
    )

    logger.debug("START lines block content ========================\n%s", content)
    logger.debug("END lines block content ==========================")
    lines: list[dict[str, Any]] = []
    current_row: dict[str, Any] = {}

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
    skip_patterns = settings.get("skip_line")
    if skip_patterns and not isinstance(skip_patterns, list):
        skip_patterns = [skip_patterns]
    for line in _regex.split(settings["line_separator"], content):
        # If the line has empty lines in it , skip them
        if not line.strip("").strip("\n").strip("\r") or not line:
            continue
        # `skip_line: pattern` or `skip_line: [pat1, pat2]` lets a template drop
        # lines that match an unwanted shape (e.g. a sub-total / VAT footer that
        # the line regex would otherwise wrongly match). Issue #652.
        if skip_patterns and any(
            _regex.search(pattern, line) for pattern in skip_patterns
        ):
            logger.debug("skip_line match on %r", line)
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
                        _regex.search(x, line) for x in settings["skip_line"]
                    ]
                else:
                    # Or a simple string
                    skip_line_results = [_regex.search(settings["skip_line"], line)]
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

    _apply_line_replace(settings, lines)

    types = settings.get("types", [])
    for row in lines:
        for name in row:
            if name in types:
                row[name] = template.coerce_type(row[name], types[name])
    return lines


def _normalize_line_replace(spec: Any) -> dict[str, list[tuple[str, str]]]:
    """Normalize a lines ``replace`` setting to {sub-field: [(pattern, repl)]}.

    Accepts a mapping ``{uom: [...], name: [...]}`` or a list of single-key
    mappings ``[{uom: [...]}, {name: [...]}]`` (each value being a single pair or
    a list of pairs, as for a field-level replace).

    Args:
        spec (Any): The raw ``replace`` value from the lines settings.

    Returns:
        dict[str, list[tuple[str, str]]]: Per-sub-field replacement pairs.
    """
    if not spec:
        return {}
    raw: dict[str, Any] = {}
    if isinstance(spec, dict):
        raw = spec
    else:
        for entry in spec:
            raw.update(entry)
    return {field: _normalize_replacements(pairs) for field, pairs in raw.items()}


def _apply_line_replace(settings: dict[str, Any], lines: list[dict[str, Any]]) -> None:
    """Apply per-sub-field ``replace`` to each line row in place (issue #497).

    Lets a lines/tables template map captured sub-field values, e.g. units of
    measure ``PS`` -> ``unit``, before type coercion.

    Args:
        settings (dict[str, Any]): The lines settings (may hold ``replace``).
        lines (list[dict[str, Any]]): The parsed rows, mutated in place.
    """
    replace_map = _normalize_line_replace(settings.get("replace"))
    if not replace_map:
        return
    for row in lines:
        for field, replacements in replace_map.items():
            if field in row:
                row[field] = _replace_value(row[field], replacements)


def parse_by_rule(
    template: "InvoiceTemplate",
    field: str,
    rule: dict[str, Any],
    content: str,
) -> list[dict[str, Any]]:
    """Parse lines from a block of text based on a rule.

    Args:
        template (InvoiceTemplate): The template dictionary.
        field (str): The field name.
        rule (dict[str, Any]): The rule dictionary.
        content (str): The text content to parse.

    Returns:
        list[dict[str, Any]]: The parsed lines.
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
        start = _regex.search(settings["start"], content)
        if not start:
            logger.debug("Failed to find lines block start")
            break
        content = content[start.end() :]

        end = _regex.search(settings["end"], content)
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
    template: "InvoiceTemplate",
    field: str,
    settings: dict[str, Any],
    content: str,
) -> list[dict[str, Any]]:
    """Parse lines from the content based on the given settings.

    Args:
        template (InvoiceTemplate): The template dictionary.
        field (str): The field name.
        settings (dict[str, Any]): The settings dictionary.
        content (str): The text content to parse.

    Returns:
        list[dict[str, Any]]: The parsed lines.
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
    match: Match[str] | None, current_row: dict[str, Any]
) -> dict[str, Any]:
    """Parse the current row data.

    Args:
        match (Match[str] | None): The match object.
        current_row (dict[str, Any]): The current row dictionary.

    Returns:
        dict[str, Any]: The updated current row dictionary.
    """
    if match:
        for field, value in match.groupdict().items():
            current_row[field] = "%s%s%s" % (
                current_row.get(field, ""),
                (current_row.get(field, "") and "\n") or "",
                value.strip() if value else "",
            )
    return current_row
