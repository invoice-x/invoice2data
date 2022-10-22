# -*- coding: utf-8 -*-
# Run: python -m unittest tests.test_lib

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file,
#    usually at the bottom.

# https://docs.python.org/3.10/library/unittest.html#test-cases

import os

try:
    from StringIO import StringIO  # noqa: F401
except ImportError:
    from io import StringIO  # noqa: F401
import unittest

from invoice2data.main import extract_data
from invoice2data.input import pdftotext, tesseract, pdfminer_wrapper, pdfplumber
from invoice2data.output import to_csv, to_json, to_xml
from .common import get_sample_files


def _extract_data_for_export():
    pdf_files = get_sample_files('.pdf')
    for file in pdf_files:
        if file.endswith("oyo.pdf"):
            res = [extract_data(file, None)]
            return res


class TestLIB(unittest.TestCase):
    def test_extract_data(self):
        pdf_files = get_sample_files('.pdf')
        for file in pdf_files:
            res = extract_data(file, None)
            print(res)  # Check why logger.info is not working, for the time being using print
            self.assertTrue(type(res) is dict, "return is not a dict")

    def test_extract_data_pdftotext(self):
        pdf_files = get_sample_files('.pdf')
        for file in pdf_files:
            try:
                res = extract_data(file, None, pdftotext)
                print(res)  # Check why logger.info is not working, for the time being using print
            except ImportError:
                # print("pdftotext module not installed!")
                self.assertTrue(False, "pdftotext is not installed")
            self.assertTrue(type(res) is dict, "return is not a dict")

    def test_output_json(self):
        dump_dict = _extract_data_for_export()
        print(dump_dict)
        file_path = "invoices-output-for-test.json"
        to_json.write_to_file(dump_dict, file_path)
        self.assertTrue(os.path.exists(file_path), "File not made")
        os.remove(file_path)

    def test_output_xml(self):
        dump_dict = _extract_data_for_export()
        print(dump_dict)
        file_path = "invoices-output-for-test.xml"
        to_xml.write_to_file(dump_dict, file_path)
        self.assertTrue(os.path.exists(file_path), "File not made")
        os.remove(file_path)

    def test_output_csv(self):
        dump_dict = _extract_data_for_export()
        print(dump_dict)
        file_path = "invoices-output-for-test.csv"
        to_csv.write_to_file(dump_dict, file_path)
        self.assertTrue(os.path.exists(file_path), "File not made")
        os.remove(file_path)

    def test_extract_data_pdfminer(self):
        pdf_files = get_sample_files('.pdf')
        for file in pdf_files:
            print("Testing pdfminer with file", file)
            try:
                res = extract_data(file, None, pdfminer_wrapper)
                print(res)  # Check why logger.info is not working, for the time being using print
            except ImportError:
                # print("pdfminer module not installed!")
                self.assertTrue(False, "pdfminer is not installed")
                self.assertTrue(type(res) is str, "return is not a string")

    def test_extract_data_pdfplumber(self):
        pdf_files = get_sample_files('.pdf')
        for file in pdf_files:
            extract_data(file, None, pdfplumber)

    def test_tesseract_for_return(self):
        png_files = get_sample_files('.png')
        for file in png_files:
            if tesseract.to_text(file) is None:
                self.assertTrue(False, "Tesseract returned None")
            else:
                self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
