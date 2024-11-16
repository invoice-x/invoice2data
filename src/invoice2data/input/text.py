# SPDX-License-Identifier: MIT


def to_text(path):
    with open(path) as f:
        return f.read()
