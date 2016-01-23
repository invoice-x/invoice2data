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
from invoice2data.templates import read_templates

class TestExtraction(unittest.TestCase):

    def setUp(self):
        self.templates = read_templates(
            pkg_resources.resource_filename('invoice2data', 'templates'))

    def test_external_pdfs(self):
        file_folder = os.getenv('EXTERNAL_PDFS', None)
        if file_folder:
            for path, subdirs, files in os.walk(file_folder):
                for file in files:
                    extract_data(os.path.join(path, file), self.templates)            

    def test_internal_pdfs(self):
        file_folder = pkg_resources.resource_filename(__name__, 'pdfs')
        for path, subdirs, files in os.walk(file_folder):
            for file in files:
                extract_data(os.path.join(path, file), self.templates)          

if __name__ == '__main__':
    unittest.main()
