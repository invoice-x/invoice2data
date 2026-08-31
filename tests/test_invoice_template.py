import unittest
from typing import Any

import pytest

from invoice2data.extract.invoice_template import InvoiceTemplate


pytestmark = pytest.mark.windows_strict


def test_template_with_exclude_keyword_is_not_matched() -> None:
    optimized_str = "Basic Test Which should not pass because of the word Exclude_this"
    invoicetempl = InvoiceTemplate(
        [
            ("keywords", ["Basic Test"]),
            ("exclude_keywords", ["Exclude_this"]),
            ("template_name", "excludekeywordnotlist.yml"),
            ("priority", 5),
            ("issuer", "Basic Test"),
        ]
    )
    template_matched = InvoiceTemplate.matches_input(invoicetempl, optimized_str)
    assert template_matched is False, "A template with exclude keywords is not matched"


def test_skip_template_with_too_long_lang_code() -> None:
    options_test: dict[str, list[str]] = {
        "currency": ["EUR"],
        "date_formats": [],
        "languages": ["aaa"],
        "decimal_separator": ["."],
        "replace": [],
    }

    tpl: dict[str, Any] = {}
    tpl["keywords"] = ["Basic Test"]
    tpl["exclude_keywords"] = []
    tpl["options"] = options_test
    tpl["template_name"] = ["3_char_langcode.yml"]
    try:
        InvoiceTemplate(tpl)
    except Exception:
        assert True, (
            "Template with language code length != 2 characters is not initiated"
        )
    else:
        raise AssertionError(  # Raise AssertionError here
            "Template with language code length != 2 characters is initiated"
        )


class TestInvoiceTemplateMethods(unittest.TestCase):
    def test_replace_a_with_b(self) -> None:
        options_test: dict[str, Any] = {
            "currency": ["EUR"],
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ["."],
            "replace": [["a", "b"]],
        }

        tpl: dict[str, Any] = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = options_test
        tpl["template_name"] = "replace_a_with_b"
        invoicetempl = InvoiceTemplate(tpl)
        extracted_str = "a"
        print("InvoiceTempl: \n%s" % invoicetempl)

        optimized_str = invoicetempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s" % optimized_str)
        self.assertEqual(optimized_str, "b")

    def test_remove_accents(self) -> None:
        options_test: dict[str, Any] = {
            "currency": ["EUR"],
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ["."],
            "remove_accents": True,
        }

        tpl: dict[str, Any] = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = options_test
        tpl["template_name"] = "test_remove_accents"
        invoicetempl = InvoiceTemplate(tpl)
        extracted_str = "é€$%^&*@!.a Málaga François Phút Hơn 中文"
        print("InvoiceTempl: \n%s" % invoicetempl)

        optimized_str = invoicetempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s\n" % optimized_str)
        self.assertEqual(
            optimized_str,
            "e€$%^&*@!.a Malaga Francois Phut Hon 中文",
            "Remove accents function failed, output not equal",
        )

    def test_remove_whitespace(self) -> None:
        options_test: dict[str, Any] = {
            "currency": ["EUR"],
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ["."],
            "remove_whitespace": True,
        }

        tpl: dict[str, Any] = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = options_test
        tpl["template_name"] = "test_remove_whitespace"
        invoicetempl = InvoiceTemplate(tpl)
        extracted_str = "a    b"
        print("InvoiceTempl: \n%s" % invoicetempl)

        optimized_str = invoicetempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s\n" % optimized_str)
        self.assertEqual(optimized_str, "ab", "remove whitespace test failed")

    def test_lowercase(self) -> None:
        options_test: dict[str, Any] = {
            "currency": ["EUR"],
            "date_formats": [],
            "languages": ["aa"],
            "decimal_separator": ["."],
            "lowercase": True,
        }

        tpl: dict[str, Any] = {}
        tpl["keywords"] = ["Basic Test"]
        tpl["exclude_keywords"] = []
        tpl["options"] = options_test
        tpl["template_name"] = "test_lowercase"
        invoicetempl = InvoiceTemplate(tpl)
        extracted_str = "ABCD"
        print("InvoiceTempl: \n%s" % invoicetempl)

        optimized_str = invoicetempl.prepare_input(extracted_str)
        print("extracted_str: \n%s" % extracted_str)
        print("optimized_str: \n%s\n" % optimized_str)
        self.assertEqual(optimized_str, "abcd", "Lowercase test failed")


def _currency_template(fields: dict[str, Any], name: str) -> InvoiceTemplate:
    """Build an InvoiceTemplate with the four required fields stubbed in."""
    base_fields: dict[str, Any] = {
        "issuer": "Any Vendor Ltd",
        "date": {"parser": "regex", "regex": r"Date:\s+(\S+)", "type": "date"},
        "amount": {"parser": "regex", "regex": r"Total:\s+([\d.]+)", "type": "float"},
        "invoice_number": {"parser": "regex", "regex": r"Invoice #(\d+)"},
        **fields,
    }
    tpl: dict[str, Any] = {
        "keywords": ["Any Vendor Ltd"],
        "exclude_keywords": [],
        "options": {
            "currency": "EUR",
            "date_formats": [],
            "languages": ["en"],
            "decimal_separator": ".",
            "replace": [],
        },
        "template_name": name,
        "fields": base_fields,
    }
    return InvoiceTemplate(tpl)


def test_extracted_currency_survives_extract() -> None:
    """Regression: dynamic currency extraction must not be clobbered.

    ``output["currency"] = self.options["currency"]`` used to unconditionally
    overwrite any currency captured by a template field with the template's
    static option (default "EUR"), silently defeating dynamic currency
    extraction. ``setdefault`` now preserves the extracted value.
    """
    tpl = _currency_template(
        {"currency": {"parser": "regex", "regex": r"Currency:\s+(\w{3})"}},
        "currency_capture.yml",
    )
    extracted = tpl.extract(
        "Any Vendor Ltd\nInvoice #42\nDate: 2026-01-01\nTotal: 12.50\nCurrency: USD",
        invoice_file="/dev/null",
        input_module=None,
    )
    assert extracted["currency"] == "USD", (
        f"template's static currency={tpl.options['currency']!r} clobbered "
        f"the extracted value; got {extracted['currency']!r}"
    )


def test_missing_currency_falls_back_to_option() -> None:
    """No `currency` field extracted -> the option's default is emitted."""
    tpl = _currency_template({}, "currency_default.yml")
    extracted = tpl.extract(
        "Any Vendor Ltd\nInvoice #42\nDate: 2026-01-01\nTotal: 12.50",
        invoice_file="/dev/null",
        input_module=None,
    )
    assert extracted["currency"] == "EUR"


def _keyword_template(
    keywords: list[str], excludes: list[str] | None = None
) -> InvoiceTemplate:
    """Build a minimal template with the given keywords / exclude_keywords."""
    return InvoiceTemplate(
        {
            "template_name": "kw.yml",
            "keywords": keywords,
            "exclude_keywords": excludes or [],
        }
    )


class TestMatchesInputRegex:
    """Issue #742: keywords / exclude_keywords are regex, not plain substrings."""

    def test_plain_string_keyword_still_matches(self) -> None:
        assert _keyword_template(["Acme Corp"]).matches_input("Hello Acme Corp inv#1")

    def test_regex_whitespace_metachar_matches_multiple_spaces(self) -> None:
        r"""`Company\s+US` should match `Company    US` (multi-space)."""
        assert _keyword_template([r"Company\s+US"]).matches_input(
            "Invoice from Company    US"
        )

    def test_regex_alternation_matches_either_branch(self) -> None:
        r"""`Company\s+(US|UK)` should match either branch."""
        tpl = _keyword_template([r"Company\s+(US|UK)"])
        assert tpl.matches_input("Company US invoice")
        assert tpl.matches_input("Company UK invoice")
        assert not tpl.matches_input("Company CA invoice")

    def test_case_insensitive_flag_prefix_matches(self) -> None:
        """`(?i)Accor` should match `accor`, `ACCOR`, `Accor`."""
        tpl = _keyword_template(["(?i)Accor"])
        assert tpl.matches_input("hotel accor invoice")
        assert tpl.matches_input("HOTEL ACCOR invoice")

    def test_exclude_keyword_is_also_regex(self) -> None:
        """`exclude_keywords: (?i)draft` blocks the template on `DRAFT`/`draft`."""
        tpl = _keyword_template(["Acme"], ["(?i)draft"])
        assert not tpl.matches_input("Acme DRAFT invoice")
        assert tpl.matches_input("Acme final invoice")

    def test_invalid_regex_falls_back_to_substring(self) -> None:
        """A stray `[` isn't valid regex but should still match literally."""
        # `Company [Ltd]` is invalid regex (unclosed character class after group),
        # but plenty of legacy templates might include unescaped brackets/parens.
        # Fallback: literal substring.
        tpl = _keyword_template(["Company [Ltd"])
        assert tpl.matches_input("Payment to Company [Ltd for services")
        assert not tpl.matches_input("Payment to Company Ltd for services")


if __name__ == "__main__":
    unittest.main()
