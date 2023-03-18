"""
Plugin to extract tables from an invoice.
"""

import re
import logging

logger = logging.getLogger(__name__)

DEFAULT_OPTIONS = {"field_separator": r"\s+", "line_separator": r"\n"}


def extract(self, content, output):
    """Try to extract tables from an invoice"""

    for table in self["tables"]:

        # First apply default options.
        plugin_settings = DEFAULT_OPTIONS.copy()
        plugin_settings.update(table)
        table = plugin_settings

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

        if not start or not end:
            logger.warning("no table body found - start %s, end %s", start, end)
            continue
        types = table.get("types", [])

        table_body = content[start.end() : end.start()]
        logger.debug("START table body content ========================")
        logger.debug(table_body)
        logger.debug("END table body content ==========================")
        logger.debug(f"Regex pattern = {table['body']}")

        for line in re.split(table["line_separator"], table_body):
            # if the line has empty lines in it , skip them
            if not line.strip("").strip("\n") or not line:
                continue

            match = re.search(table["body"], line)
            if match:
                for field, value in match.groupdict().items():
                    # If a field name already exists, do not overwrite it
                    if field in output:
                        continue

                    if field.startswith("date") or field.endswith("date"):
                        output[field] = self.parse_date(value)
                        if not output[field]:
                            logger.error("Date parsing failed on date '%s'", value)
                            return None
                    elif field.startswith("amount"):
                        output[field] = self.parse_number(value)
                    elif field.name in types:
                        output[field] = template.coerce_type(output[field], types[name])
                    else:
                        output[field] = value
            logger.debug("ignoring *%s* because it doesn't match anything", line)
