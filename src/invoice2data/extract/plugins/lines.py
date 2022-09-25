"""
Plugin to extract individual lines from an invoice.

This plugin has been replaced by the "lines" parser. All new templates
should use the parser instead. It's provided for backward compatibility
only.
"""

from .. import parsers


def extract(self, content, output):
    lines = []

    rules = self['lines']
    if not isinstance(self['lines'], list):
        rules = [rules]

    for rule in rules:
        lines += parsers.lines.parse(self, "lines", rule, content)

    if len(lines):
        output["lines"] = lines
