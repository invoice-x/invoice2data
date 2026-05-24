"""This module abstracts templates for invoice providers.

Templates are initially read from .yml files and then kept as class.
"""

import unicodedata
from collections import OrderedDict as OrderedDictType
from logging import getLogger
from pprint import pformat
from typing import Any

from ..input import extract_text
from ..input import supports_area
from . import _dates
from . import _regex
from . import parsers
from . import schema
from .plugins import camelot
from .plugins import lines
from .plugins import tables


logger = getLogger(__name__)

#: Dedicated logger for the optimized_str dump, so `--debug-optimized-str` can show
#: just that (without the rest of the debug noise) by raising this logger alone.
optimized_str_logger = getLogger("invoice2data.optimized_str")


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

PARSERS_MAPPING = {
    "lines": parsers.lines,
    "regex": parsers.regex,
    "static": parsers.static,
}

PLUGIN_MAPPING = {"lines": lines, "tables": tables, "camelot": camelot}


class InvoiceTemplate(OrderedDictType[str, Any]):
    """Represents single template files that live as .yml files on the disk.

    Methods:
      prepare_input(extracted_str)
          Input raw string
          and perform transformations, as set in the template file.
      matches_input(extracted_str)
          Check if the string matches keywords set in the template file.
      parse_number(value)
          Parse number, remove decimal separator and add other options.
      parse_date(value)
          Parse date and return the date after parsing.
      coerce_type(value, target_type)
          Change the type of values.
      extract(optimized_str)
          Given a template file and a string, extract matching data fields.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Merge template-specific options with defaults
        self.options: dict[str, Any] = OPTIONS_DEFAULT.copy()

        if "options" in self:
            self.options.update(self["options"])

        languages = self.options.get("languages", [])

        if not isinstance(languages, list):
            languages = [languages]

        for lang in self.options.get("languages", []):  # type: ignore [attr-defined]
            if len(lang) != 2:
                raise AssertionError(
                    "Error in Template %s lang code must have 2 letters"
                    % self["template_name"]
                )

        # Set issuer, if it doesn't exist.
        if "issuer" not in self.keys():
            self["issuer"] = self["keywords"][0]

    def prepare_input(self, extracted_str: str) -> str:
        """Input raw string and do transformations, as set in template file."""
        # Remove whitespace
        if self.options["remove_whitespace"]:
            optimized_str = _regex.sub(" +", "", extracted_str)
        else:
            optimized_str = extracted_str

        # Remove accents
        if self.options["remove_accents"]:
            optimized_str = _regex.sub(
                "[\u0300-\u0362]", "", unicodedata.normalize("NFKD", optimized_str)
            )

        # Convert to lower case
        if self.options["lowercase"]:
            optimized_str = optimized_str.lower()

        if not isinstance(self.options.get("replace", []), list):
            self.options["replace"] = [self.options["replace"]]

        # Specific replace
        for replace in self.options.get("replace", []):
            assert len(replace) == 2, (
                "Error in Template %s A replace should be a list of exactly 2 elements."
                % self["template_name"]
            )
            optimized_str = _regex.sub(replace[0], replace[1], optimized_str)

        return optimized_str

    def matches_input(self, extracted_str: str) -> bool:
        """Check if the extracted string matches the template keywords.

        Args:
            extracted_str (str): The extracted text from the invoice.

        Returns:
            bool: True if the extracted string matches the template keywords,
                False otherwise.
        """
        if all(keyword in extracted_str for keyword in self["keywords"]):
            # All keywords found
            if self["exclude_keywords"] and any(
                exclude_keyword in extracted_str
                for exclude_keyword in self["exclude_keywords"]
            ):
                # At least one exclude_keyword found
                logger.debug(
                    "Template: %s | Keywords matched. Exclude keyword found!",
                    self["template_name"],
                )
                return False
            # No exclude_keywords or none found, template is good
            logger.debug(
                "Template: %s | Keywords matched. No exclude keywords found.",
                self["template_name"],
            )
            return True
        logger.debug(
            "Template: %s | Failed to match all keywords.", self["template_name"]
        )
        return False

    def parse_number(self, value: str) -> float:
        """Parses a number from a string.

        This function parses a numerical value from a string, handling
        different decimal separators and thousands separators based on locale.

        Args:
            value (str): The string containing the number to be parsed.

        Returns:
            float: The parsed numerical value.
        """
        assert isinstance(value, str)
        # Early exit if no thousands separator or custom decimal separator is present
        if not any(char in value for char in r",.'\s"):
            return float(value)

        # Ensure decimal_separator is a string before calling count()
        assert isinstance(self.options["decimal_separator"], str)
        assert value.count(self.options["decimal_separator"]) < 2, (
            f"Error in Template {self['template_name']}: "
            "Decimal separator cannot be present several times"
        )

        # Determine the thousands separator based on the decimal separator
        thousands_separator = "," if self.options["decimal_separator"] == "." else "."

        # Remove all possible thousands separators
        amount_no_thousand_sep = _regex.sub(
            r"[\s']", "", value.replace(thousands_separator, "")
        )

        # Replace the decimal separator with a dot
        return float(
            amount_no_thousand_sep.replace(str(self.options["decimal_separator"]), ".")
        )

    def parse_date(self, value: str) -> Any:
        """Parses date and returns date after parsing."""
        res = _dates.parse_date(
            value,
            tuple(self.options["date_formats"] or ()),
            tuple(self.options["languages"] or ()),
        )
        logger.debug("result of date parsing=%s", res)
        return res

    def coerce_type(self, value: str, target_type: str) -> Any:
        """Coerces a value to the specified target type.

        Args:
            value (str): The value to be coerced.
            target_type (str): The target type to which the value should be coerced.
                                  Valid values: 'int', 'float', 'date'.

        Returns:
            Any: The coerced value.

        Raises:
            AssertionError: If the target_type is unknown.
        """
        if target_type == "int":
            if not value:
                return 0
            return int(self.parse_number(value))
        if target_type == "float":
            if not value:
                return 0.0
            return float(self.parse_number(value))
        if target_type == "date" or target_type == "datetime":
            return self.parse_date(value)
        raise AssertionError("Unknown type")

    def extract(
        self, optimized_str: str, invoice_file: str, input_module: Any
    ) -> dict[str, Any]:
        """Extracts data from the optimized string using the template.

        Args:
            optimized_str (str): The optimized string.
            invoice_file (str): The path to the invoice file.
            input_module (Any): The input module used.

        Returns:
            dict[str, Any]: The extracted data.

        """
        output = _initialize_output_and_log(self, optimized_str)

        for k, v in self["fields"].items():
            if isinstance(v, dict):
                optimized_str_for_parser = _handle_area(
                    self, v, input_module, invoice_file, optimized_str
                )

                if "parser" in v:
                    _handle_parser(self, k, v, optimized_str_for_parser, output)

            elif k.startswith("static_"):
                logger.debug("field=%s | static value=%s", k, v)
                output[k.replace("static_", "")] = v

            else:
                _handle_legacy_syntax(self, k, v, optimized_str, output)
        output["currency"] = self.options["currency"]

        # Run plugins (invoice_file is needed by path-based plugins like camelot):
        for plugin_keyword, plugin_func in PLUGIN_MAPPING.items():
            if plugin_keyword in self.keys():
                plugin_func.extract(self, optimized_str, output, invoice_file)
        # Normalise line/tax_line field names to the canonical vocabulary before
        # any computation/validation runs on them.
        schema.normalize_line_fields(output)
        _compute_line_tax(output)
        _validate_tax_total(output, self["template_name"])
        _validate_fields(self, output)
        return _check_required_fields(self, output)


def _initialize_output_and_log(
    self: InvoiceTemplate, optimized_str: str
) -> dict[str, Any]:
    """Initialize the output dictionary and log debug information."""
    optimized_str_logger.debug(
        "START optimized_str ========================\n%s", optimized_str
    )
    optimized_str_logger.debug("END optimized_str ==========================")
    logger.debug(
        "Date parsing: languages=%s date_formats=%s",
        self.options["languages"],
        self.options["date_formats"],
    )
    logger.debug(
        "Float parsing: decimal separator=[%s]", self.options["decimal_separator"]
    )
    logger.debug("keywords=%s", self["keywords"])
    logger.debug(self.options)

    output = {}
    output["issuer"] = self["issuer"]
    # Expose which template matched, for downstream tooling (issue #618).
    output["template_name"] = self.get("template_name", "")
    return output


def _handle_area(
    self: InvoiceTemplate,
    v: dict[str, Any],
    input_module: Any,
    invoice_file: str,
    optimized_str: str,
) -> str:
    """Handle area-specific extraction."""
    if "area" in v and supports_area(input_module):
        logger.debug(f"Area was specified with parameters {v['area']}")
        optimized_str_area: str = extract_text(input_module, invoice_file, v["area"])
        logger.debug(
            "START pdftotext area result ===========================\n%s",
            optimized_str_area,
        )
        logger.debug("END pdftotext area result =============================")
        return optimized_str_area
    return optimized_str


def _handle_parser(
    self: InvoiceTemplate,
    k: str,
    v: dict[str, Any],
    optimized_str_for_parser: str,
    output: dict[str, Any],
) -> None:
    """Handle parsing using different parsers."""
    if v["parser"] in PARSERS_MAPPING:
        parser = PARSERS_MAPPING[v["parser"]]
        value = parser.parse(self, k, v, optimized_str_for_parser)
        if value or value == 0.0:
            output[k] = value
        else:
            logger.warning("Failed to parse field %s with parser %s", k, v["parser"])
    else:
        logger.error("Field %s has unknown parser %s set", k, v["parser"])


def _handle_legacy_syntax(
    self: InvoiceTemplate, k: str, v: Any, optimized_str: str, output: dict[str, Any]
) -> None:
    """Handle legacy syntax for backward compatibility."""
    result = None
    if k.startswith("sum_amount") and type(v) is list:
        k = k[4:]
        result = parsers.regex.parse(
            self, k, {"regex": v, "type": "float", "group": "sum"}, optimized_str, True
        )
    elif k.startswith("date") or k.endswith("date"):
        result = parsers.regex.parse(
            self, k, {"regex": v, "type": "date"}, optimized_str, True
        )
    elif k.startswith("amount"):
        result = parsers.regex.parse(
            self, k, {"regex": v, "type": "float"}, optimized_str, True
        )
    else:
        result = parsers.regex.parse(self, k, {"regex": v}, optimized_str, True)

    if result or result == 0.0:
        output[k] = result
    else:
        logger.warning("regexp for field %s didn't match", k)


def _compute_line_tax(output: dict[str, Any]) -> None:
    """Fill in a missing ``line_tax_amount`` for ``tax_lines`` rows.

    For each per-rate row in ``tax_lines`` that has ``line_tax_percent`` and
    ``price_subtotal`` but no ``line_tax_amount``, compute it as
    ``round(price_subtotal * line_tax_percent / 100, 2)``. Existing values are
    never overwritten. (Product ``lines`` are left untouched.)

    Args:
        output (dict[str, Any]): The extracted-fields dictionary, modified in place.
    """
    rows = output.get("tax_lines")
    if not isinstance(rows, list):
        return
    for row in rows:
        if not isinstance(row, dict):
            continue
        if (
            "line_tax_amount" not in row
            and "line_tax_percent" in row
            and "price_subtotal" in row
        ):
            try:
                percent = float(row["line_tax_percent"])
                subtotal = float(row["price_subtotal"])
            except (TypeError, ValueError):
                continue
            row["line_tax_amount"] = round(subtotal * percent / 100, 2)


def _validate_tax_total(output: dict[str, Any], template_name: str) -> None:
    """Warn if the per-rate tax amounts don't add up to ``amount_tax``.

    Purely advisory (a tolerance-based warning); never raises or alters output.

    Args:
        output (dict[str, Any]): The extracted-fields dictionary.
        template_name (str): Template name, for the log message.
    """
    tax_lines = output.get("tax_lines")
    amount_tax = output.get("amount_tax")
    if not isinstance(tax_lines, list) or not isinstance(amount_tax, int | float):
        return
    total = sum(
        row["line_tax_amount"]
        for row in tax_lines
        if isinstance(row, dict) and isinstance(row.get("line_tax_amount"), int | float)
    )
    if total and abs(total - amount_tax) > 0.02:
        logger.warning(
            "tax_lines total (%.2f) does not match amount_tax (%.2f) in %s",
            total,
            amount_tax,
            template_name,
        )


def _validate_fields(self: InvoiceTemplate, output: dict[str, Any]) -> None:
    """Validate output field names against the canonical schema.

    Quiet by default: only warns when an unrecognized field looks like a typo of
    a canonical name. With the template option ``strict_fields: true`` it raises
    on any unrecognized field (except those listed in ``options.extra_fields``).

    Args:
        self (InvoiceTemplate): The template instance.
        output (dict[str, Any]): The extracted-fields dictionary.

    Raises:
        ValueError: If ``strict_fields`` is set and unrecognized fields remain.
    """
    extra = self.options.get("extra_fields", []) or []
    issues = schema.validate_output(output, extra_fields=extra)
    if not issues:
        return
    if self.options.get("strict_fields", False):
        names = ", ".join(name for name, _ in issues)
        raise ValueError(
            f"Unrecognized fields in template {self['template_name']}: {names}"
        )
    for name, suggestion in issues:
        if suggestion:
            logger.warning(
                "Field '%s' is not a recognized field; did you mean '%s'? (%s)",
                name,
                suggestion,
                self["template_name"],
            )
        else:
            logger.debug(
                "Field '%s' is not a canonical field (%s)", name, self["template_name"]
            )


def _check_required_fields(
    self: InvoiceTemplate, output: dict[str, Any]
) -> dict[str, Any]:
    """Check if all required fields are present in the output."""
    if "required_fields" not in self.keys():
        required_fields = ["date", "amount", "invoice_number", "issuer"]
    else:
        required_fields = []
        for v in self["required_fields"]:
            required_fields.append(v)

    if set(required_fields).issubset(output.keys()):
        output["desc"] = "Invoice from %s" % (self["issuer"])
        logger.debug("\n %s", pformat(output, indent=2))
        return output
    fields = list(set(output.keys()))
    logger.error(
        "Unable to match all required fields. "
        f"The required fields are: {required_fields}. "
        f"Output contains the following fields: {fields}."
    )
    missing = set(required_fields) - set(fields)
    raise ValueError(f"Unable to parse required field(s): {missing}")
