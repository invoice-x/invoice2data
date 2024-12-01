"""text input module for invoice2data."""

# SPDX-License-Identifier: MIT


def to_text(path: str) -> str:
    """Reads the content of a text file.

    Args:
      path (str): The path to the text file.

    Returns:
      str: The content of the text file.
    """
    with open(path) as f:
        return f.read()
