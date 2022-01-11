# SPDX-License-Identifier: MIT

"""
Interface for fields parsers.

Parsers are basic modules used for extracting data. They are responsible
for parsing invoice text using specified settings. Depending on a parser
and settings it may be e.g.:
1. Looking for a single value
2. Grouping multiple occurences (e.g. summing up)
3. Finding repeating parts (e.g. multiple rows)

Each parser is a module (file) in the package `parsers` and provides at
a minimum the `parse` function with those arguments:

def parse(template, field, settings, content)

Parser has to return a single value (e.g. number, date, string, array)
or None in case of error. Such a value will be included in the output.
"""
