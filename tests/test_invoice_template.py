
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
    assert (
        template_matched is False
    ), "A template with exclude keywords is not matched"


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
        assert True, "Template with language code length != 2 characters is not initiated"
    else:
        print("InvoiceTempl is\n%s" % InvoiceTempl)
        debug = InvoiceTempl["options"]
        print("debug is\n%s" % debug)
        assert False, "Template class initiated with language code length other then 2"
