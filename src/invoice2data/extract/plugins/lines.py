"""
Plugin to extract individual lines from an invoice.

This plugin has been replaced by the "lines" parser. All new templates
should use the parser instead. It's provided for backward compatibility
only.
"""

from .. import parsers


def extract(self, content, output):
    lines = parsers.lines.parse(self, "lines", self["lines"], content)
    if lines is not None:
        output["lines"] = lines
