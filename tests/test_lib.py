# Run: python -m unittest tests.test_lib

# Or: python -m unittest discover

# 1. You define your own class derived from unittest.TestCase.
# 2. Then you fill it with functions that start with 'test_'
# 3. You run the tests by placing unittest.main() in your file,
#    usually at the bottom.

# https://docs.python.org/3.10/library/unittest.html#test-cases


import os
import shutil
import unittest
from io import StringIO  # noqa: F401
from typing import Any
from unittest import mock

from invoice2data import Invoice2Data
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


needs_pdfplumber = unittest.skipIf(
    not have_pdfplumber(), reason="requires pdfplumber\n"
)


def _extract_data_for_export() -> list[dict[str, Any]]:
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
                    res: str | dict[str, Any] = extract_data(
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

    @needs_pdfplumber
    def test_pdfplumber_to_text_not_empty(self) -> None:
        # Regression: to_text() used to always return "" because it threw away
        # the per-page extraction and re-derived text from a dict that never had
        # a "text" key. Guard against the backend silently going dead again.
        pdf_files = get_sample_files(".pdf")
        for file in pdf_files:
            if not file.endswith("FlipkartInvoice.pdf"):
                continue
            text = pdfplumber.to_text(file)
            self.assertGreater(
                len(text.strip()),
                0,
                f"pdfplumber.to_text returned empty text for {file}",
            )

    @unittest.skipUnless(shutil.which("tesseract"), "tesseract not installed")
    def test_tesseract_for_return(self) -> None:
        png_files = get_sample_files(".png")
        for file in png_files:
            if tesseract.to_text(file) is None:
                self.assertTrue(False, "Tesseract returned None")
            else:
                self.assertTrue(True)

    def test_invoice2data_class(self) -> None:
        i2d = Invoice2Data()
        self.assertTrue(len(i2d.templates) > 0, "no built-in templates loaded")
        for file in get_sample_files(".pdf"):
            if file.endswith("oyo.pdf"):
                res = i2d.extract_data(file)
                self.assertEqual(res.get("issuer"), "OYO")

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


class TestBackendCascade(unittest.TestCase):
    """Cover the input-backend cascade and template-declared ``input_module``."""

    def test_resolve_readers_default_cascade(self) -> None:
        from invoice2data.__main__ import DEFAULT_INPUT_READERS
        from invoice2data.__main__ import _resolve_readers

        readers = _resolve_readers("x.pdf", None)
        # pdftotext leads the default cascade; every reader is an available
        # member of the configured default list.
        self.assertEqual(readers[0], pdftotext)
        self.assertTrue(all(r in DEFAULT_INPUT_READERS for r in readers))

    def test_resolve_readers_txt_uses_text_backend(self) -> None:
        from invoice2data.__main__ import _resolve_readers
        from invoice2data.input import text as text_module

        self.assertEqual(_resolve_readers("x.txt", None), [text_module])

    def test_resolve_readers_explicit_overrides_cascade(self) -> None:
        from invoice2data.__main__ import _resolve_readers
        from invoice2data.input import pdfium

        self.assertEqual(_resolve_readers("x.pdf", "pdfium"), [pdfium])
        self.assertEqual(_resolve_readers("x.pdf", pdftotext), [pdftotext])

    def test_preferred_module_honours_template_pin(self) -> None:
        from invoice2data.__main__ import _preferred_module
        from invoice2data.extract.invoice_template import InvoiceTemplate
        from invoice2data.input import pdfium

        tmpl = InvoiceTemplate(
            {
                "template_name": "pinned",
                "keywords": ["x"],
                "exclude_keywords": [],
                "input_module": "pdfium",
            }
        )
        # A different backend matched first -> switch to the pinned one.
        self.assertIs(_preferred_module(tmpl, used=pdftotext), pdfium)
        # Already on the pinned backend -> no switch.
        self.assertIsNone(_preferred_module(tmpl, used=pdfium))

    def test_preferred_module_none_without_pin(self) -> None:
        from invoice2data.__main__ import _preferred_module
        from invoice2data.extract.invoice_template import InvoiceTemplate

        tmpl = InvoiceTemplate(
            {"template_name": "plain", "keywords": ["x"], "exclude_keywords": []}
        )
        self.assertIsNone(_preferred_module(tmpl, used=pdftotext))

    def test_safe_to_text_swallows_backend_errors(self) -> None:
        from invoice2data.__main__ import _safe_to_text

        # A missing file makes the backend raise; the cascade must see "".
        self.assertEqual(_safe_to_text(pdftotext, "/no/such/file.pdf"), "")


if __name__ == "__main__":
    unittest.main()
