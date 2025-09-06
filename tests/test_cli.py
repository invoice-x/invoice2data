# -*- coding: utf-8 -*-
# Run: python -m unittest tests.test_cli

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file,
#    usually at the bottom.

# https://docs.python.org/3.10/library/unittest.html#test-cases

import csv
import datetime
import json
import os
import shutil
import sys
import unittest
from typing import Any
from typing import Dict
from xml.dom import minidom

import pytest
from invoice2data.__main__ import main
from invoice2data.extract.loader import read_templates

from .common import exclude_template, get_sample_files, inputparser_specific


def ocrmypdf_available() -> bool:
    try:
        import ocrmypdf  # type: ignore[import-not-found] # noqa: F401
    except ImportError:
        return False
    return True


needs_ocrmypdf = unittest.skipIf(not ocrmypdf_available(), reason="requires ocrmypdf")
skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Tesseract executable cannot be found in Windows test environment. FIXME",
)


class TestCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.templates = read_templates()

    def compare_json_content(self, test_file: str, json_file: str) -> Any:
        """Compares the content of two JSON files.

        Args:
            test_file (str): Path to the first JSON file.
            json_file (str): Path to the second JSON file.

        Returns:
            bool: True if the content is identical, False otherwise.
        """
        with open(test_file) as json_test_file, open(json_file) as json_json_file:
            jdatatest = json.load(json_test_file)
            jdatajson = json.load(json_json_file)
            return jdatajson == jdatatest

    def test_input(self) -> None:
        """Tests the --input-reader argument."""
        with self.assertRaises(SystemExit) as cm:
            main(["--input-reader", "pdftotext", *get_sample_files(".pdf")])
        self.assertEqual(cm.exception.code, 0)

    def test_output_name(self) -> None:
        """Tests the --output-name argument."""
        test_file = "inv_test_8asd89f78a9df.csv"
        exclude_list = ["AzureInterior.pdf"]
        test_list = exclude_template(get_sample_files(".pdf"), exclude_list)
        args = ["--output-name", test_file, "--output-format", "csv", *test_list]

        with self.assertRaises(
            SystemExit
        ) as cm:  # Use assertRaises with a context manager
            main(args)

        self.assertEqual(
            cm.exception.code, 0
        )  # Assert that the exit code is 0 (success)

        self.assertTrue(os.path.exists(test_file))
        os.remove(test_file)

    def test_debug(self) -> None:
        """Tests the --debug argument."""
        with self.assertRaises(SystemExit) as cm:
            main(["--debug", *get_sample_files(".pdf")])
        self.assertEqual(cm.exception.code, 0)

    # TODO: move result comparison to own test module.
    # TODO: parse output files instead of comparing them byte-by-byte.

    @skip_on_windows
    def test_content_json(self):
        """Tests the JSON output content."""
        input_files = get_sample_files((".pdf", ".txt"))
        tests_templ_folder = "./tests/custom/templates"
        json_files = get_sample_files(".json")
        test_files = "test_compare.json"
        for ifile in input_files:
            for jfile in json_files:
                if ifile[:-4] == jfile[:-5]:
                    with self.assertRaises(SystemExit) as cm:
                        main(
                            [
                                "--output-name",
                                test_files,
                                "--output-format",
                                "json",
                                "--template-folder",
                                tests_templ_folder,
                                ifile,
                            ]
                        )
                    self.assertEqual(cm.exception.code, 0)
                    compare_verified = self.compare_json_content(test_files, jfile)
                    print(compare_verified)
                    if not compare_verified:
                        self.assertTrue(
                            False, "Failed to verify parsing result for " + jfile
                        )
                    os.remove(test_files)

    @skip_on_windows
    def test_output_format_date_json(self):
        """Tests the date format in JSON output."""
        pdf_files = get_sample_files("free_fiber.pdf")
        test_file = "test_compare.json"
        for pfile in pdf_files:
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "--output-name",
                        test_file,
                        "--output-format",
                        "json",
                        "--output-date-format",
                        "%d/%m/%Y",
                        pfile,
                    ]
                )
            self.assertEqual(cm.exception.code, 0)
            with open(test_file) as json_test_file:
                jdatatest = json.load(json_test_file)
            compare_verified = (jdatatest[0]["date"] == "02/07/2015") and (
                jdatatest[0]["date_due"] == "05/07/2015"
            )
            print(compare_verified)
            if not compare_verified:
                self.assertTrue(False, "Unexpected date format")
            os.remove(test_file)

    def test_output_format_date_csv(self) -> None:
        """Tests the date format in CSV output."""
        pdf_files = get_sample_files("free_fiber.pdf")
        test_file = "test_compare.csv"
        for pfile in pdf_files:
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "--output-name",
                        test_file,
                        "--output-format",
                        "csv",
                        "--output-date-format",
                        "%d/%m/%Y",
                        pfile,
                    ]
                )
            self.assertEqual(cm.exception.code, 0)
            with open(test_file) as csv_test_file:
                csvdatatest = csv.DictReader(csv_test_file, delimiter=",")
                for row in csvdatatest:
                    compare_verified = (row["date"] == "02/07/2015") and (
                        row["date_due"] == "05/07/2015"
                    )
                    print(compare_verified)
                    if not compare_verified:
                        self.assertTrue(False, "Unexpected date format")
            os.remove(test_file)

    @skip_on_windows
    def test_output_format_date_xml(self):
        """Tests the date format in XML output."""
        pdf_files = get_sample_files("free_fiber.pdf")
        test_file = "test_compare.xml"
        for pfile in pdf_files:
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "--output-name",
                        test_file,
                        "--output-format",
                        "xml",
                        "--output-date-format",
                        "%d/%m/%Y",
                        pfile,
                    ]
                )
            self.assertEqual(cm.exception.code, 0)
            with open(test_file) as xml_test_file:
                xmldatatest = minidom.parse(xml_test_file)  # noqa
            dates = xmldatatest.getElementsByTagName("date")
            compare_verified = dates[0].firstChild.data == "02/07/2015"  # type: ignore
            print(compare_verified)
            if not compare_verified:
                self.assertTrue(False, "Unexpected date format")
            os.remove(test_file)

    @skip_on_windows
    def test_copy(self):
        """Tests the --copy argument."""
        directory = os.path.dirname("tests/copy_test/pdf/")
        # make sure directory is deleted
        shutil.rmtree("tests/copy_test/", ignore_errors=True)
        os.makedirs(directory)

        exclude_list = ["AzureInterior.pdf"]
        test_list = exclude_template(get_sample_files(".pdf"), exclude_list)

        with self.assertRaises(SystemExit) as cm:
            main(["--copy", "tests/copy_test/pdf", *test_list])
        self.assertEqual(cm.exception.code, 0)
        # Use os.walk to count files in the directory
        qty_copied_files = 0
        for _, _, files in os.walk(os.path.abspath("tests/copy_test/pdf")):
            qty_copied_files += len(files)

        print("test_copy - Amount of copied files %s" % qty_copied_files)
        print("test_copy - test_list length", len(test_list))
        shutil.rmtree("tests/copy_test/", ignore_errors=True)
        self.assertEqual(qty_copied_files, len(test_list))

    def test_exclude_template(self) -> None:
        """Tests the --exclude-built-in-templates argument."""
        compare_folder = os.path.dirname("tests/compare/")
        for path, _subdirs, files in os.walk(compare_folder):
            for file in files:
                if file.endswith("oyo.pdf"):
                    my_file = os.path.join(path, file)
        directory = os.path.dirname("tests/temp_test/")
        os.makedirs(directory)
        shutil.copy(
            "src/invoice2data/extract/templates/com/com.oyo.invoice.yml",
            "tests/temp_test/",
        )
        with self.assertRaises(SystemExit) as cm:
            main(
                [
                    "--exclude-built-in-templates",
                    "--template-folder",
                    directory,
                    my_file,
                ]
            )
        self.assertEqual(cm.exception.code, 0)
        shutil.rmtree(directory, ignore_errors=True)

    def get_filename_format_test_data(self, filename_format: str) -> Dict[str, Any]:
        """Generates test input and expected output by walking the compare dir.

        Args:
            filename_format (str): The filename format string.

        Returns:
            Dict[str, Any]: A dictionary of test data.
        """
        data: Dict[str, Any] = {}
        compare_folder = os.path.dirname("tests/compare/")
        for path, _subdirs, files in os.walk(compare_folder):
            for file in files:
                root, ext = os.path.splitext(file)
                if "AzureInterior" in file:
                    continue
                if inputparser_specific(file):
                    print("input parser specific file found!!!")
                    continue
                if root not in data:
                    data[root] = {}
                if file.endswith((".pdf", ".txt")):
                    data[root]["input_fpath"] = os.path.join(path, file)
                if file.endswith(".json"):
                    with open(os.path.join(path, file)) as f:
                        res = json.load(f)[0]
                        date = datetime.datetime.strptime(res["date"], "%Y-%m-%d")
                        data[root]["output_fname"] = filename_format.format(
                            date=date.strftime("%Y-%m-%d"),
                            invoice_number=str(
                                res["invoice_number"]
                            ),  # Convert to string
                            desc=res["desc"],
                        )
        return data

    @skip_on_windows
    def test_copy_with_default_filename_format(self):
        """Tests the --copy argument with the default filename format."""
        copy_dir = os.path.join("tests", "copy_test", "pdf")
        # make sure directory is deleted
        shutil.rmtree(os.path.dirname(copy_dir), ignore_errors=True)
        filename_format = "{date} {invoice_number} {desc}.pdf"

        data: Dict[str, Any] = self.get_filename_format_test_data(filename_format)

        os.makedirs(copy_dir)

        sample_files = [v["input_fpath"] for k, v in data.items()]

        with self.assertRaises(SystemExit) as cm:
            main(
                [
                    "--copy",
                    copy_dir,  # Pass the copy_dir as an argument
                    *sample_files,
                ]
            )
        self.assertEqual(cm.exception.code, 0)

        self.assertTrue(
            all(
                os.path.exists(os.path.join(copy_dir, v["output_fname"]))
                for k, v in data.items()
            )
        )

        shutil.rmtree(os.path.dirname(copy_dir), ignore_errors=True)

    @skip_on_windows
    def test_copy_with_custom_filename_format(self):
        """Tests the --copy argument with a custom filename format."""
        copy_dir = os.path.join("tests", "copy_test", "pdf")
        filename_format = "Custom Prefix {date} {invoice_number}.pdf"

        data: Dict[str, Any] = self.get_filename_format_test_data(filename_format)

        os.makedirs(copy_dir)

        sample_files = [v["input_fpath"] for k, v in data.items()]

        with self.assertRaises(SystemExit) as cm:
            main(
                [
                    "--copy",
                    copy_dir,
                    "--filename-format",
                    filename_format,
                    *sample_files,
                ]
            )
        self.assertEqual(cm.exception.code, 0)

        self.assertTrue(
            all(
                os.path.exists(os.path.join(copy_dir, v["output_fname"]))
                for k, v in data.items()
            )
        )

        shutil.rmtree(os.path.dirname(copy_dir), ignore_errors=True)

    @skip_on_windows
    def test_area(self):
        """Tests the --area argument."""
        pdf_files = get_sample_files("NetpresseInvoice.pdf")
        test_file = "test_area.json"
        for pfile in pdf_files:
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "--output-name",
                        test_file,
                        "--output-format",
                        "json",
                        "--output-date-format",
                        "%Y-%m-%d",
                        pfile,
                    ]
                )
            self.assertEqual(cm.exception.code, 0)
            with open(test_file) as json_test_file:
                jdatatest = json.load(json_test_file)
            compare_verified = jdatatest[0]["date"] == "2022-11-28"
            if not compare_verified:
                self.assertTrue(False, "Failure in area rule")
            os.remove(test_file)

    # advanced test case (saeco)
    # Where the pdf has to be ocr'd first
    # before any keywords can be matched

    @skip_on_windows
    @needs_ocrmypdf
    def test_ocrmypdf(self) -> None:
        """Tests the ocrmypdf input reader."""
        pdf_files = get_sample_files("saeco.pdf", exclude_input_specific=False)
        test_file = "test_ocrmypdf.json"
        for pfile in pdf_files:
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "--output-name",
                        test_file,
                        "--input-reader",
                        "ocrmypdf",
                        "--output-format",
                        "json",
                        "--output-date-format",
                        "%Y-%m-%d",
                        pfile,
                    ]
                )
            self.assertEqual(cm.exception.code, 0)
            with open(test_file) as json_test_file:
                jdatatest = json.load(json_test_file)
            compare_verified = jdatatest[0]["date"] == "2022-09-08"
            if not compare_verified:
                self.assertTrue(False, "Failure in ocrmypdf test")
            os.remove(test_file)

    # Test the fallback from pdf to text to ocrmypdf.
    # with ocrmypdf installed

    @skip_on_windows
    @needs_ocrmypdf
    def test_fallback_with_ocrmypdf(self) -> None:
        """Tests the fallback from pdftotext to ocrmypdf."""
        pdf_files = get_sample_files("saeco.pdf", exclude_input_specific=False)
        test_file = "test_fallback_ocrmypdf.json"
        for pfile in pdf_files:
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "--output-name",
                        test_file,
                        "--input-reader",
                        "pdftotext",
                        "--output-format",
                        "json",
                        "--output-date-format",
                        "%Y-%m-%d",
                        "--debug",
                        pfile,
                    ]
                )
            self.assertEqual(cm.exception.code, 0)
            with open(test_file) as json_test_file:
                jdatatest = json.load(json_test_file)
                print(jdatatest)
            if jdatatest:
                compare_verified = jdatatest[0]["date"] == "2022-09-08"
                if not compare_verified:
                    self.assertTrue(
                        False,
                        "Failure in fallback to ocrmypdf test with ocrmypdf installed",
                    )
                os.remove(test_file)
            else:
                self.fail("No data extracted from the file")


if __name__ == "__main__":
    unittest.main()
