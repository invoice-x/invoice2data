"""Utility functions for testing."""

import logging
import os
from typing import List


# Reduce log level of various modules
logging.getLogger("pdfminer").setLevel(logging.WARNING)


def get_sample_files(extension: str, exclude_input_specific: bool = True) -> List[str]:
    """Get the  sample files.

    Args:
        extension (str): The extension of the files to get.
        exclude_input_specific (bool, optional): Whether to exclude input-specific files. Defaults to True.

    Returns:
        List[str]: A list of paths to the sample files.
    """
    compare_files = []
    compare_folder = os.path.dirname("./tests/compare")
    for path, _subdirs, files in os.walk(compare_folder):
        for file in files:
            if exclude_input_specific and inputparser_specific(file):
                continue
            if file.endswith(extension):
                compare_files.append(os.path.join(path, file))
    return compare_files


def exclude_template(test_list: List[str], exclude_list: List[str]) -> List[str]:
    """Exclude specific templates from the list.

    Args:
        test_list (List[str]): The list of templates to filter.
        exclude_list (List[str]): The list of templates to exclude.

    Returns:
        List[str]: The filtered list of templates.
    """
    return [
        elem
        for elem in test_list
        if not any(elem.endswith(end) for end in exclude_list)
    ]


def inputparser_specific(file: str) -> bool:
    """Checks if a file requires a specific input parser.

    Args:
        file (str): The name of the file.

    Returns:
        bool: True if the file requires a specific input parser, False otherwise.
    """
    return file.startswith("saeco")
