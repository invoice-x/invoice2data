# -*- coding: utf-8 -*-
# file pyquasar_test.py
# Run: python -m unittest test.pyquasar_test

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file,
#    usually at the bottom.

# https://docs.python.org/2/library/unittest.html#test-cases

import unittest
import pkg_resources
import os

from invoice2data.main import extract_data
from invoice2data.template import read_templates

class TestExtraction(unittest.TestCase):

    def setUp(self):
        self.templates = read_templates(
            pkg_resources.resource_filename('invoice2data', 'templates'))

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

if __name__ == '__main__':
    unittest.main()
