"""
This module abstracts templates for invoice providers.

Templates are initially read from .yml files and then kept as class.
"""

import re
import dateparser
import unicodedata
import logging
from collections import OrderedDict
from . import parsers
from .plugins import lines, tables
# Area extraction is currently added for pdftotext and tesseract (which uses pdftotext)
from ..input import pdftotext, tesseract
from typing import Optional

logger = logging.getLogger(__name__)

OPTIONS_DEFAULT = {
    "remove_whitespace": False,
    "remove_accents": False,
    "lowercase": False,
    "currency": "EUR",
    "date_formats": [],
    "languages": [],
    "decimal_separator": ".",
    "replace": [],  # example: see templates/fr/fr.free.mobile.yml
}

PARSERS_MAPPING = {"lines": parsers.lines, "regex": parsers.regex, "static": parsers.static}

PLUGIN_MAPPING = {"lines": lines, "tables": tables}


class InvoiceTemplate(OrderedDict):
    """
    Represents single template files that live as .yml files on the disk.

    Methods
    -------
    prepare_input(extracted_str)
        Input raw string and do transformations, as set in template file.
    matches_input(optimized_str)
        See if string matches keywords set in template file
    parse_number(value)
        Parse number, remove decimal separator and add other options
    parse_date(value)
        Parses date and returns date after parsing
    coerce_type(value, target_type)
        change type of values
    extract(optimized_str)
        Given a template file and a string, extract matching data fields.
    """

    def __init__(self, *args, **kwargs):
        super(InvoiceTemplate, self).__init__(*args, **kwargs)

        # Merge template-specific options with defaults
        self.options = OPTIONS_DEFAULT.copy()

        for lang in self.options["languages"]:
            assert len(lang) == 2, "lang code must have 2 letters"

        if "options" in self:
            self.options.update(self["options"])

        # Set issuer, if it doesn't exist.
        if "issuer" not in self.keys():
            self["issuer"] = self["keywords"][0]

    def prepare_input(self, extracted_str: str) -> str:
        """
        Input raw string and do transformations, as set in template file.
        """

        # Remove whitespace
        if self.options["remove_whitespace"]:
            optimized_str = re.sub(" +", "", extracted_str)
        else:
            optimized_str = extracted_str

        # Remove accents
        if self.options["remove_accents"]:
            optimized_str = unicodedata.normalize('NFKC', optimized_str).encode('ascii', 'ignore').decode('ascii')

        # Convert to lower case
        if self.options["lowercase"]:
            optimized_str = optimized_str.lower()

        # Specific replace
        for replace in self.options["replace"]:
            assert len(replace) == 2, "A replace should be a list of exactly 2 elements."
            optimized_str = re.sub(replace[0], replace[1], optimized_str)

        return optimized_str

    def matches_input(self, optimized_str: str) -> bool:
        """See if string matches all keyword patterns and no exclude_keyword patterns set in template file.

        Args:
        optimized_str: String of the text from OCR of the pdf after applying options defined in the template.

        Return:
        Boolean
            - True if all keywords are found and none of the exclude_keywords are found.
            - False if either not all keywords are found or at least one exclude_keyword is found."""

        if all([re.search(keyword, optimized_str) for keyword in self["keywords"]]):
            # All keyword patterns matched
            if self["exclude_keywords"]:
                if any([re.search(exclude_keyword, optimized_str) for exclude_keyword in self["exclude_keywords"]]):
                    # At least one exclude_keyword matches
                    logger.debug("Template: %s. Keywords matched. Exclude keyword found!", self["template_name"])
                    return False
            # No exclude_keywords or none match, template is good
            logger.debug("Template: %s. Keywords matched. No exclude keywords found.", self["template_name"])
            return True
        else:
            logger.debug("Template: %s. Failed to match all keywords.", self["template_name"])
            return False

    def parse_number(self, value):
        assert (
            value.count(self.options["decimal_separator"]) < 2
        ), "Decimal separator cannot be present several times"
        # replace decimal separator by a |
        amount_pipe = value.replace(self.options["decimal_separator"], "|")
        # remove all possible thousands separators
        amount_pipe_no_thousand_sep = re.sub(r"[.,'\s]", "", amount_pipe)
        # put dot as decimal sep
        return float(amount_pipe_no_thousand_sep.replace("|", "."))

    def parse_date(self, value):
        """Parses date and returns date after parsing"""
        res = dateparser.parse(
            value,
            date_formats=self.options["date_formats"],
            languages=self.options["languages"],
        )
        logger.debug("result of date parsing=%s", res)
        return res

    def coerce_type(self, value, target_type):
        if target_type == "int":
            if not value.strip():
                return 0
            return int(self.parse_number(value))
        elif target_type == "float":
            if not value.strip():
                return 0.0
            return float(self.parse_number(value))
        elif target_type == "date":
            return self.parse_date(value)
        assert False, "Unknown type"

    def extract(self, optimized_str: str, invoice_file: str, input_module: str) -> Optional[dict]:
        """
        Given a template file and a string, extract matching data fields.

        Args:
        optimized_str: String of the full text from pdf with template options applied.
        invoice_file: String of the path to the file being processed.
            - This is used when processing areas
        input_module: String of the input module to be used for pdf conversion
            - This is used when processing areas

        Returns:
        Dictionary of results if all required fields were found.
        None if required fields are missing.
        """
        logger.debug("START optimized_str ========================\n" + optimized_str)
        logger.debug("END optimized_str ==========================")
        logger.debug(
            "Date parsing: languages=%s date_formats=%s",
            self.options["languages"],
            self.options["date_formats"],
        )
        logger.debug(
            "Float parsing: decimal separator=%s", self.options["decimal_separator"]
        )
        logger.debug("keywords=%s", self["keywords"])
        logger.debug(self.options)

        # Try to find data for each field.
        output = {}
        output["issuer"] = self["issuer"]

        for k, v in self["fields"].items():
            # k is the key of the field
            # v is the value
            if isinstance(v, dict):
                # Options were supplied to this field
                if "area" in v and input_module in (pdftotext, tesseract):
                    # Area is currently only supported for pdftotext
                    # area is optional and re-extracts the text being searched
                    # This obviously has a performance impact, so use wisely
                    # Verify that the input_module is set to pdftotext ... this is the only one included right now
                    logger.debug(f"Area was specified with parameters {v['area']}")
                    # Extract the text for the specified area
                    # Do NOT overwrite optimized_str. We're inside a loop and it will affect all other fields!
                    optimized_str_area = input_module.to_text(invoice_file, v['area']).decode("utf-8")
                    # Log the text
                    logger.debug("START pdftotext area result ===========================")
                    logger.debug(optimized_str_area)
                    logger.debug("END pdftotext area result =============================")
                    optimized_str_for_parser = optimized_str_area
                else:
                    # No area specified
                    optimized_str_for_parser = optimized_str
                if "parser" in v:
                    # parser is required and may require additional options
                    # e.g. "parser: regex" requires "regex: [pattern]"
                    if v["parser"] in PARSERS_MAPPING:
                        parser = PARSERS_MAPPING[v["parser"]]
                        value = parser.parse(self, k, v, optimized_str_for_parser)
                        if value is not None:
                            output[k] = value
                        else:
                            logger.error("Failed to parse field %s with parser %s", k, v["parser"])
                    else:
                        logger.warning("Field %s has unknown parser %s set", k, v["parser"])
                else:
                    logger.warning("Field %s doesn't have parser specified", k)
            elif k.startswith("static_"):
                logger.debug("field=%s | static value=%s", k, v)
                output[k.replace("static_", "")] = v
            else:
                # Legacy syntax support (backward compatibility)
                result = None
                if k.startswith("sum_amount") and type(v) is list:
                    k = k[4:]
                    result = parsers.regex.parse(self, k, {"regex": v, "type": "float", "group": "sum"}, optimized_str,
                                                 True)
                elif k.startswith("date") or k.endswith("date"):
                    result = parsers.regex.parse(self, k, {"regex": v, "type": "date"}, optimized_str, True)
                elif k.startswith("amount"):
                    result = parsers.regex.parse(self, k, {"regex": v, "type": "float"}, optimized_str, True)
                else:
                    result = parsers.regex.parse(self, k, {"regex": v}, optimized_str, True)

                if result is None:
                    logger.warning("regexp for field %s didn't match", k)
                else:
                    output[k] = result

        output["currency"] = self.options["currency"]

        # Run plugins:
        for plugin_keyword, plugin_func in PLUGIN_MAPPING.items():
            if plugin_keyword in self.keys():
                plugin_func.extract(self, optimized_str, output)

        # If required fields were found, return output, else log error.
        if "required_fields" not in self.keys():
            required_fields = ["date", "amount", "invoice_number", "issuer"]
        else:
            required_fields = []
            for v in self["required_fields"]:
                required_fields.append(v)

        if set(required_fields).issubset(output.keys()):
            output["desc"] = "Invoice from %s" % (self["issuer"])
            logger.debug(output)
            return output
        else:
            fields = list(set(output.keys()))
            logger.error(
                "Unable to match all required fields. "
                "The required fields are: {0}. "
                "Output contains the following fields: {1}.".format(
                    required_fields, fields
                )
            )
            return None
