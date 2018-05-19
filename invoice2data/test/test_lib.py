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


class TestCLI(unittest.TestCase):
    def setUp(self):
        # self.templates = read_templates()
        # vself.parser = create_parser()
        pass

    def _get_test_file_pdf_path(self):
        out_files = []
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
            for file in files:
                if file.endswith(".pdf"):
                    out_files.append(os.path.join(path, file))
        return out_files

    def _get_test_file_img_path(self):
        out_files = []
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
            for file in files:
                if file.endswith(".png"):
                    out_files.append(os.path.join(path, file))
        return out_files

    # def _get_test_file_json_path(self):
    #     compare_files = []
    #     for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
    #         for file in files:
    #             if file.endswith(".json"):
    #                 compare_files.append(os.path.join(path, file))
    #     return compare_files

    # def compare_json_content(self, test_file, json_file):
    #     with open(test_file) as json_test_file, open(json_file) as json_json_file:
    #         jdatatest = json.load(json_test_file)
    #         jdatajson = json.load(json_json_file)
    #     if jdatajson == jdatatest:
    #         logger.info("True")
    #         return True
    #     else:
    #         logger.info("False")
    #         return False

    # def test_content_json(self):
    #     pdf_files = self._get_test_file_pdf_path()
    #     json_files = self._get_test_file_json_path()
    #     test_files = 'test_compare.json'
    #     for pfile in pdf_files:
    #         for jfile in json_files:
    #             if pfile[:-4] == jfile[:-5]:
    #                 args = self.parser.parse_args(
    #                     ['--output-name', test_files, '--output-format', 'json', pfile])
    #                 main(args)
    #                 compare_verified = self.compare_json_content(test_files, jfile)
    #                 print(compare_verified)
    #                 if not compare_verified:
    #                     self.assertTrue(False)
    #                 os.remove(test_files)
    #     self.assertTrue(True)

    def test_extract_data(self):
        pdf_files = self._get_test_file_pdf_path()
        for file in pdf_files:
            res = extract_data(file, None)
            print(res)  # Check why logger.info is not working, for the time being using print
            self.assertTrue(type(res) is dict, "return is not a dict")

    def test_extract_data_pdftotext(self):
        pdf_files = self._get_test_file_pdf_path()
        for file in pdf_files:
            try:
                res = extract_data(file, None, pdftotext)
                print(res)  # Check why logger.info is not working, for the time being using print
            except ImportError:
                # print("pdftotext module not installed!")
                self.assertTrue(False, "pdftotext is not installed")
            self.assertTrue(type(res) is dict, "return is not a dict")

    # def test_extract_data_pdfminer(self):
    #     pdf_files = self._get_test_file_pdf_path()
    #     for file in pdf_files:
    #         res = extract_data(file, None, pdfminer)
    #         print(res)  # Check why logger.info is not working, for the time being using print
    #         self.assertTrue(False, "pdfminer is not installed")
    #     self.assertTrue(type(res) is dict, "return is not a dict")

    def test_extract_data_pdfminer(self):
        pdf_files = self._get_test_file_pdf_path()
        for file in pdf_files:
            try:
                res = extract_data(file, None, pdfminer)
                print(res)  # Check why logger.info is not working, for the time being using print
            except ImportError:
                self.assertTrue(False, "pdfminer is not installed")
            self.assertTrue(type(res) is dict, "return is not a dict")

    # def test_extract_data_tesseract(self):
    #     img_files = self._get_test_file_img_path()
    #     for file in img_files:
    #         try:
    #             res = extract_data(file, None, tesseract)
    #             print(res)  # Check why logger.info is not working, for the time being using print
    #         except (ModuleNotFoundError, FileNotFoundError):
    #             # print("Tesseract module not installed!")
    #             self.assertTrue(False, "tesseract is not installed")
    #         self.assertTrue(type(res) is dict, "return is not a dict")


if __name__ == '__main__':
    unittest.main()
