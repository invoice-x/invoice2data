# SPDX-License-Identifier: MIT

"""
Pseudo-parser returning a static (predefined) value
"""


def parse(template, settings, content):
    if "value" not in settings:
        return None
    return settings["value"]
