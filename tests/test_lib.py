# Run: python -m unittest tests.test_lib

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file,
#    usually at the bottom.

# https://docs.python.org/3.10/library/unittest.html#test-cases


import os
import sys
import pytest
import unittest
from io import StringIO  # noqa: F401
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from unittest import mock

from invoice2data.__main__ import extract_data
from invoice2data.input import ocrmypdf
from invoice2data.input import pdfminer_wrapper
from invoice2data.input import pdfplumber
from invoice2data.input import pdftotext
from invoice2data.input import tesseract
from invoice2data.output import to_csv
from invoice2data.output import to_json
from invoice2data.output import to_xml

from .common import get_sample_files


def have_pdfplumber() -> bool:
    try:
        import pdfplumber  # type: ignore[import-not-found] # noqa: F401
    except ImportError:
        return False
    return True


needs_pdfplumber = unittest.skipIf(not have_pdfplumber(), reason="requires pdfplumber\n")
skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Tesseract executable cannot be found in Windows test environment. FIXME",
)


def _extract_data_for_export() -> List[Dict[str, Any]]:
    pdf_files = get_sample_files(".pdf")
    for file in pdf_files:
        if file.endswith("oyo.pdf"):
            res = [extract_data(file, [])]
            return res
    return []  # Return an empty list if no matching file is found


class TestLIB(unittest.TestCase):
    def test_extract_data(self) -> None:
        pdf_files = get_sample_files(".pdf")
        for file in pdf_files:
            res = extract_data(file, [])
            print(
                res
            )  # Check why logger.info is not working, for the time being using print
            self.assertTrue(isinstance(res, dict), "return is not a dict")

    def test_extract_data_pdftotext(self) -> None:
        pdf_files = get_sample_files(".pdf")
        for file in pdf_files:
            try:
                res = extract_data(file, [], pdftotext)
                print(
                    res
                )  # Check why logger.info is not working, for the time being using print
            except ImportError:
                # print("pdftotext module not installed!")
                self.assertTrue(False, "pdftotext is not installed")
            self.assertTrue(type(res) is dict, "return is not a dict")

    def test_output_json(self) -> None:
        dump_dict = _extract_data_for_export()
        print(dump_dict)
        file_path = "invoices-output-for-test.json"
        to_json.write_to_file(dump_dict, file_path)
        self.assertTrue(os.path.exists(file_path), "File not made")
        os.remove(file_path)

    def test_output_xml(self) -> None:
        dump_dict = _extract_data_for_export()
        print(dump_dict)
        file_path = "invoices-output-for-test.xml"
        to_xml.write_to_file(dump_dict, file_path)
        self.assertTrue(os.path.exists(file_path), "File not made")
        os.remove(file_path)

    def test_output_csv(self) -> None:
        dump_dict = _extract_data_for_export()
        print(dump_dict)
        file_path = "invoices-output-for-test.csv"
        to_csv.write_to_file(dump_dict, file_path)
        self.assertTrue(os.path.exists(file_path), "File not made")
        os.remove(file_path)

    def test_extract_data_pdfminer(self) -> None:
        pdf_files = get_sample_files(".pdf")
        for file in pdf_files:
            if file.endswith("NetpresseInvoice.pdf"):
                print("Testing pdfminer with file", file)
                try:
                    res: Union[str, Dict[str, Any]] = extract_data(
                        file, None, pdfminer_wrapper
                    )
                    print(res)
                except ImportError:
                    self.assertTrue(False, "pdfminer is not installed")
                    self.assertTrue(type(res) is str, "return is not a string")

    @needs_pdfplumber
    def test_extract_data_pdfplumber(self) -> None:
        pdf_files = get_sample_files(".pdf")
        for file in pdf_files:
            if not file.endswith("FlipkartInvoice.pdf"):
                continue
            print("Testing pdfplumber with file", file)
            extract_data(file, [], pdfplumber)

    @skip_on_windows
    def test_tesseract_for_return(self):
        png_files = get_sample_files('.png')
        for file in png_files:
            if tesseract.to_text(file) is None:
                self.assertTrue(False, "Tesseract returned None")
            else:
                self.assertTrue(True)

    def test_ocrmypdf_available_unavailable(self) -> None:
        with mock.patch.dict("sys.modules", {"ocrmypdf": None}):
            have = ocrmypdf.ocrmypdf_available()
            print("ocrmypdf should not be available have is %s" % have)
            self.assertFalse(have, "ocrmypdf is NOT installed")

    def test_haveocrmypdf_available(self) -> None:
        with mock.patch.dict("sys.modules", {"ocrmypdf": True}):
            have = ocrmypdf.ocrmypdf_available()
            print("ocrmypdf should be available have is %s" % have)
            self.assertTrue(have, "ocrmypdf is installed")


if __name__ == "__main__":
    unittest.main()