# file pyquasar_test.py
# Run: python -m unittest test.pyquasar_test

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file, usually at the bottom.

# https://docs.python.org/2/library/unittest.html#test-cases

import unittest
import pkg_resources
from os import listdir
from os.path import isfile, join

from ..main import extract_data

class TestExtraction(unittest.TestCase):

    def setUp(self):
        pass

    def test_sample_pdfs(self):
        pass

    def test_extraction(self):
        file_folder = pkg_resources.resource_filename(__name__, 'pdfs')
        pdfs = [ join(file_folder, f) for f in listdir(file_folder) if isfile(join(file_folder, f)) ]

        for pdf in pdfs:
            print extract_data(pdf)

if __name__ == '__main__':
    unittest.main()

