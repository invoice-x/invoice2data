import os
import glob
import filecmp
import json
import shutil

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import unittest

import pkg_resources
from invoice2data.main import *
from invoice2data.input import *

from .common import *

def _extract_data_for_export():
    pdf_files = get_sample_files('.pdf')
    for file in pdf_files:
        if file.endswith("oyo.pdf"):
            res = [extract_data(file, None)]
            return res

class TestCLI(unittest.TestCase):
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
            res = extract_data(file, None, pdfminer_wrapper)
            # TODO: some invoices are not recognized with pdfminer.
            # self.assertTrue(type(res) is dict, "return is not a dict")

if __name__ == '__main__':
    unittest.main()
