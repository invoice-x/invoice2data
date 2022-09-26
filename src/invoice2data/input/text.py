# SPDX-License-Identifier: MIT

def to_text(path):
    with open(path, 'r') as f:
        return f.read().encode('utf-8')
