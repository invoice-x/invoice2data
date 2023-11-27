#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Plugin to extract tables from an invoice.
"""

import re
from logging import getLogger

logger = getLogger(__name__)

DEFAULT_OPTIONS = {"field_separator": r"\s+", "line_separator": r"\n"}


def extract(self, content, output):
    """Try to extract tables from an invoice"""

    for i, table in enumerate(self["tables"]):
        # First apply default options.

        plugin_settings = DEFAULT_OPTIONS.copy()
        plugin_settings.update(table)
        table = plugin_settings
        logger.debug("Testing Rules set #%s", i)

        # Validate settings
        assert "start" in table, (
            "Error in Template %s Table start regex missing" % self["template_name"]
        )
        assert "end" in table, (
            "Error in Template %s Table end regex missing" % self["template_name"]
        )
        assert "body" in table, (
            "Error in Template %s Table body regex missing" % self["template_name"]
        )

        start = re.search(table["start"], content)
        end = re.search(table["end"], content)

        if not start:
            logger.debug("Failed to find the start of the table")
            continue

        if not end:
            logger.debug("Failed to find the end of the table")
            continue
        types = table.get("types", [])

        table_body = content[start.end() : end.start()]
        logger.debug(
            "START table body content ========================\n%s", table_body
        )
        logger.debug("END table body content ==========================")

        no_match_found = True
        for line in re.split(table["line_separator"], table_body):
            # if the line has empty lines in it , skip them

            if not line.strip("").strip("\n") or line.isspace():
                continue

            match = re.search(table["body"], line)
            if match:
                no_match_found = False
                for field, value in match.groupdict().items():
                    # If a field name already exists, do not overwrite it

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
                        output[field] = self.parse_date(value)
                        if not output[field]:
                            logger.error("Date parsing failed on date *%s*", value)
                            return None
                    elif field.startswith("amount"):
                        output[field] = self.parse_number(value)
                    elif field in types:
                        output[field] = self.coerce_type(value, types[field])
                    else:
                        output[field] = value
            else:
                logger.debug("The following line doesn't match anything:\n*%s*"
                             , line)
        if no_match_found:
            logger.debug("\033[1;43mWarning\033[0m regex=\033[91m*%s*\033[0m doesn't match anything!"
                         , table["body"])
