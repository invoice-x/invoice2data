# Run: python -m unittest tests.test_extraction

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file,
#    usually at the bottom.

# https://docs.python.org/3.10/library/unittest.html#test-cases

import datetime
import json
import os
import unittest
from pathlib import Path
from typing import Union

from invoice2data.__main__ import extract_data
from invoice2data.extract.loader import read_templates


class TestExtraction(unittest.TestCase):
    def setUp(self) -> None:
        self.templates = read_templates()

    def _run_test_on_folder(
        self, folder: Union[str, Path]
    ) -> None:  # Use Union for Python < 3.10
        for path, _subdirs, files in os.walk(folder):
            for f in files:
                res = extract_data(os.path.join(path, f), self.templates)
                print(f, res)

    def test_external_pdfs(self) -> None:
        folder = os.getenv("EXTERNAL_PDFS")
        if folder:
            self._run_test_on_folder(folder)

    def test_internal_pdfs(self) -> None:
        folder = Path(__file__).parent.parent / "pdfs"
        self._run_test_on_folder(folder)

    def test_custom_invoices(self) -> None:
        directory = os.path.dirname("tests/custom/templates/")
        templates = read_templates(directory)

        custom_folder = os.path.dirname("tests/custom/")
        for path, _subdirs, files in os.walk(custom_folder):
            for f in files:
                if f.endswith((".pdf", ".txt")):
                    ifile = os.path.join(path, f)
                    jfile = os.path.join(path, f[:-4] + ".json")

                    res = extract_data(ifile, templates)

                    # Check if res is a dictionary before accessing items
                    if isinstance(res, dict):
                        for key, value in res.items():
                            if isinstance(value, datetime.datetime):
                                res[key] = value.strftime("%Y-%m-%d")
                        res = [res]  # type: ignore
                        with open(jfile) as json_file:
                            ref_json = json.load(json_file)
                            self.assertTrue(
                                res == ref_json,
                                "Unexpected data extracted from " + ifile,
                            )


if __name__ == "__main__":
    unittest.main()
