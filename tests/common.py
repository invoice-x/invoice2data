"""Utility functions for testing."""

import logging
import os
from importlib.resources import files


# Reduce log level of various modules
logging.getLogger("pdfminer").setLevel(logging.WARNING)


def get_sample_files(extension: str, exclude_input_specific: bool = True) -> list:
    """Retrieves sample files with the specified extension from the 'compare' directory.

    Args:
        extension (str): The file extension to filter by.
        exclude_input_specific (bool, optional): Whether to exclude files that require
                                                specific input modules. Defaults to True.

    Returns:
        list: A list of file paths matching the specified criteria.
    """
    compare_files = []
    for file in os.listdir(files(__package__).joinpath("compare")):
        if exclude_input_specific and inputparser_specific(file):
            continue
        if file.endswith(extension):
            compare_files.append(str(files(__package__).joinpath("compare", file)))
    return compare_files


def exclude_template(test_list: list, exclude_list: list) -> list:
    """Removes files matching the exclude_list from the test_list.

    Args:
        test_list (list): The list of file paths to filter.
        exclude_list (list): The list of file names to exclude.

    Returns:
        list: The filtered list of file paths.
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
