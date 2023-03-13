import unittest
from invoice2data.extract.invoice_template import InvoiceTemplate


def test_template_with_exclude_keyword_is_not_matched():
    optimized_str = "Basic Test Which should not pass because of the word Exclude_this"
    InvoiceTempl = InvoiceTemplate(
        [
            ("keywords", ["Basic Test"]),
            ("exclude_keywords", ["Exclude_this"]),
            ("template_name", "excludekeywordnotlist.yml"),
            ("priority", 5),
            ("issuer", "Basic Test"),
        ]
    )
    template_matched = InvoiceTemplate.matches_input(InvoiceTempl, optimized_str)
    assert template_matched is False, "A template with exclude keywords is not matched"


def test_skip_template_with_too_long_lang_code():
    OPTIONS_TEST = {
        "currency": "EUR",
        "date_formats": [],
        "languages": ["aaa"],
        "decimal_separator": ".",
        "replace": [],
    }

    tpl = {}
    tpl["keywords"] = ["Basic Test"]
    tpl["exclude_keywords"] = []
    tpl["options"] = OPTIONS_TEST
    tpl["template_name"] = "3_char_langcode.yml"
    try:
        InvoiceTempl = InvoiceTemplate(tpl)
    except Exception:
        assert (
            True
        ), "Template with language code length != 2 characters is not initiated"
    else:
        print("InvoiceTempl is\n%s" % InvoiceTempl)
        debug = InvoiceTempl["options"]
        print("debug is\n%s" % debug)
        assert False, "Template class initiated with language code length other then 2"


class TestInvoiceTemplateMethods(unittest.TestCase):
    def test_replace_a_with_b(self):
        OPTIONS_TEST = {
            "currency": "EUR",
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ".",
            "replace": [["a", "b"]],
        }

        tpl = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = OPTIONS_TEST
        tpl["template_name"] = "replace_a_with_b"
        InvoiceTempl = InvoiceTemplate(tpl)
        extracted_str = "a"
        print("InvoiceTempl: \n%s" % InvoiceTempl)

        optimized_str = InvoiceTempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s" % optimized_str)
        self.assertEqual(optimized_str, "b")

    def test_remove_accents(self):
        OPTIONS_TEST = {
            "currency": "EUR",
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ".",
            "remove_accents": True,
        }

        tpl = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = OPTIONS_TEST
        tpl["template_name"] = "test_remove_accents"
        InvoiceTempl = InvoiceTemplate(tpl)
        extracted_str = "é€$%^&*@!.a Málaga François Phút Hơn 中文"
        print("InvoiceTempl: \n%s" % InvoiceTempl)

        optimized_str = InvoiceTempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s\n" % optimized_str)
        self.assertEqual(
            optimized_str,
            "e€$%^&*@!.a Malaga Francois Phut Hon 中文",
            "Remove accents function failed, output not equal",
        )

    def test_remove_whitespace(self):
        OPTIONS_TEST = {
            "currency": "EUR",
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ".",
            "remove_whitespace": True,
        }

        tpl = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = OPTIONS_TEST
        tpl["template_name"] = "test_remove_whitespace"
        InvoiceTempl = InvoiceTemplate(tpl)
        extracted_str = "a     b"
        print("InvoiceTempl: \n%s" % InvoiceTempl)

        optimized_str = InvoiceTempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s\n" % optimized_str)
        self.assertEqual(optimized_str, "ab", "remove whitespace test failed")

    def test_lowercase(self):
        OPTIONS_TEST = {
            "currency": "EUR",
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ".",
            "lowercase": True,
        }

        tpl = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = OPTIONS_TEST
        tpl["template_name"] = "test_lowercase"
        InvoiceTempl = InvoiceTemplate(tpl)
        extracted_str = "ABCD"
        print("InvoiceTempl: \n%s" % InvoiceTempl)

        optimized_str = InvoiceTempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s\n" % optimized_str)
        self.assertEqual(optimized_str, "abcd", "Lowercase test failed")


if __name__ == "__main__":
    unittest.main()
