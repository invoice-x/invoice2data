# -*- coding: utf-8 -*-
# Run: python -m unittest tests.test_extraction

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file,
#    usually at the bottom.

# https://docs.python.org/3.10/library/unittest.html#test-cases

import datetime
import json
import unittest
import pkg_resources
import os

from invoice2data.main import extract_data
from invoice2data.extract.loader import read_templates


class TestExtraction(unittest.TestCase):
    def setUp(self):
        self.templates = read_templates()

    def _run_test_on_folder(self, folder):
        for path, subdirs, files in os.walk(folder):
            for file in files:
                res = extract_data(os.path.join(path, file), self.templates)
                print(file, res)

    def test_external_pdfs(self):
        folder = os.getenv('EXTERNAL_PDFS', None)
        if folder:
            self._run_test_on_folder(folder)

    def test_internal_pdfs(self):
        folder = pkg_resources.resource_filename(__name__, 'pdfs')
        self._run_test_on_folder(folder)

    def test_custom_invoices(self):
        directory = os.path.dirname("tests/custom/templates/")
        templates = read_templates(directory)

        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'custom')):
            for file in files:
                if file.endswith(('.pdf', '.txt')):
                    ifile = os.path.join(path, file)
                    jfile = os.path.join(path, file[:-4] + '.json')

                    res = extract_data(ifile, templates)
                    for key, value in res.items():
                        if type(value) is datetime.datetime:
                            res[key] = value.strftime('%Y-%m-%d')
                    res = [res]
                    with open(jfile) as json_file:
                        ref_json = json.load(json_file)
                        self.assertTrue(res == ref_json, 'Unexpected data extracted from ' + ifile)


if __name__ == '__main__':
    unittest.main()
