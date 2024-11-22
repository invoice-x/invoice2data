#!/usr/bin/python
"""Command-line interface."""

import datetime
import logging
import os
import shutil
from copy import deepcopy
from os.path import join
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Union

import click

from invoice2data.extract.loader import read_templates

from .input import gvision
from .input import ocrmypdf
from .input import pdfminer_wrapper
from .input import pdfplumber
from .input import pdftotext
from .input import tesseract
from .input import text
from .output import to_csv
from .output import to_json
from .output import to_xml


logger = logging.getLogger()

input_mapping = {
    "pdftotext": pdftotext,
    "tesseract": tesseract,
    "pdfminer": pdfminer_wrapper,
    "pdfplumber": pdfplumber,
    "gvision": gvision,
    "text": text,
    "ocrmypdf": ocrmypdf,
}

output_mapping = {
    "csv": to_csv,
    "json": to_json,
    "xml": to_xml,
    "none": None,
}


class Color:
    """A class for terminal color codes."""

    BOLD = "\033[1m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW_BACK = "\033[1;43m"
    RED_BACK = "\033[1;41m"
    BOLD_RED = BOLD + RED
    END = "\033[0m"


class ColorLogFormatter(logging.Formatter):
    """A class for formatting colored logs."""

    FORMAT = (
        "%(prefix)s%(levelname)s:%(suffix)s%(name)s:%(prefix)s %(message)s%(suffix)s"
    )

    LOG_LEVEL_COLOR: ClassVar = {  # Annotate with ClassVar
        "DEBUG": {"prefix": "", "suffix": Color.END},
        "INFO": {"prefix": Color.BLUE, "suffix": Color.END},
        "WARNING": {"prefix": Color.YELLOW_BACK, "suffix": Color.END},
        "ERROR": {"prefix": Color.RED_BACK, "suffix": Color.END},
        "CRITICAL": {"prefix": Color.BOLD_RED, "suffix": Color.END},
    }

    def format(self, record):
        """Format log and console records with colors.

        Format log records with a default prefix and suffix
        to terminal color codes that corresponds
        to the log level name.
        """
        if not hasattr(record, "prefix"):
            record.prefix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get(
                "prefix"
            )

        if not hasattr(record, "suffix"):
            record.suffix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get(
                "suffix"
            )

        formatter = logging.Formatter(self.FORMAT)
        return formatter.format(record)


stream_handler = logging.StreamHandler()
stream_handler.setFormatter(ColorLogFormatter())
logger.propagate = False

if not logger.handlers:
    logger.addHandler(stream_handler)


def extract_data(
    invoicefile: str, templates: List[Any] = None, input_module: Any = None
) -> Union[Dict, bool]:
    """Extracts structured data from PDF/image invoices.

    This function uses the text extracted from a PDF file or image and
    pre-defined regex templates to find structured data.

    Reads template if no template assigned.
    Required fields are matches from templates.


    Args:
        invoicefile (str): Path of electronic invoice file in PDF, JPEG, PNG
                            (example: "/home/duskybomb/pdf/invoice.pdf").
        templates (List[Any], optional): List of instances of class `InvoiceTemplate`.
                                    Templates are loaded using `read_template` function in `loader.py`.
        input_module (Any, optional): Library to be used to extract text
                                         from the given `invoicefile`.
                                         Choices: {'pdftotext', 'pdfminer', 'tesseract', 'text'}.

    Returns:
        Union[Dict, bool]: Extracted and matched fields, or False if no template matches.

    Notes:
        Import the required `input_module` when using invoice2data as a library.

    See Also:
        read_template: Function to load templates.
        InvoiceTemplate: Class representing single template files that live as .yml files on the disk.

    Examples:
        When using `invoice2data` as a library:

        >>> from invoice2data.input import pdftotext
        >>> extract_data("invoice2data/test/pdfs/oyo.pdf", None, pdftotext)
        {'issuer': 'OYO', 'amount': 1939.0, 'date': datetime.datetime(2017, 12, 31, 0, 0), 'invoice_number': 'IBZY2087',
        'currency': 'INR', 'desc': 'Invoice IBZY2087 from OYO'}

    """
    if input_module is None:
        if invoicefile.lower().endswith(".txt"):
            input_module = text
        else:
            input_module = pdftotext

    extracted_str = input_module.to_text(invoicefile)
    if not isinstance(extracted_str, str) or not extracted_str.strip():
        logger.error(
            "Failed to extract text from %s using %s",
            invoicefile,
            input_module.__name__,
        )
        return False

    logger.debug(
        "START pdftotext result ===========================\n%s", extracted_str
    )
    logger.debug("END pdftotext result =============================")

    if templates is None:
        templates = read_templates()
    templates_matched = filter(lambda t: t.matches_input(extracted_str), templates)
    templates_matched = sorted(
        templates_matched, key=lambda k: k["priority"], reverse=True
    )
    if not templates_matched:
        if ocrmypdf.have_ocrmypdf() and input_module is not ocrmypdf:
            logger.debug("Text extraction failed, falling back to ocrmypdf")
            extracted_str, invoicefile, templates_matched = (
                extract_data_fallback_ocrmypdf(invoicefile, templates, input_module)
            )
            if not templates_matched:
                logger.error("No template for %s", invoicefile)
                return False
        else:
            logger.error("No template for %s", invoicefile)
            return False

    t = templates_matched[0]
    logger.info("Using %s template", t["template_name"])
    optimized_str = t.prepare_input(extracted_str)

    result = t.extract(optimized_str, invoicefile, input_module)

    # Check if the result is a dictionary before deepcopy
    if isinstance(result, dict):
        return deepcopy(result)
    else:
        logger.warning(
            "Extraction result is not a dictionary for %s. " "Skipping deepcopy.",
            invoicefile,
        )
        return result  # Return the original result without deepcopy


def extract_data_fallback_ocrmypdf(
    invoicefile, templates, input_module
):  # Add input_module parameter
    logger.debug("Trying OCR extraction with ocrmypdf")
    extracted_str = ocrmypdf.to_text(invoicefile)
    templates_matched = filter(lambda t: t.matches_input(extracted_str), templates)
    templates_matched = sorted(
        templates_matched, key=lambda k: k["priority"], reverse=True
    )

    if templates_matched and isinstance(
        templates_matched[0].extract(extracted_str, invoicefile, ocrmypdf), dict
    ):
        result = templates_matched[0].extract(extracted_str, invoicefile, ocrmypdf)
        if not isinstance(result, dict):
            logger.warning(
                "OCR result is not a dictionary for %s. Skipping deepcopy.",
                invoicefile,
            )
            return extracted_str, invoicefile, templates_matched
        return extracted_str, invoicefile, [deepcopy(templates_matched[0])]


@click.command()
@click.option(
    "--input-reader",
    "-i",
    type=click.Choice(input_mapping.keys()),
    # default="pdftotext", # bosd
    help="Choose text extraction function. Default: auto-detect between text & pdftotext",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(output_mapping.keys()),
    default="none",
    help="Choose output format. Default: none",
)
@click.option(
    "--output-date-format",
    "-d",
    default="%Y-%m-%d",
    help="Choose output date format. Default: %%Y-%%m-%%d (ISO 8601 Date)",
)
@click.option(
    "--output-name",
    "-o",
    default="invoices-output",
    help="Custom name for output file. Extension is added based on chosen format.",
)
@click.option("--debug", is_flag=True, help="Enable debug information.")
@click.option(
    "--copy", "-c", help="Copy and rename processed PDFs to specified folder."
)
@click.option(
    "--move", "-m", help="Move and rename processed PDFs to specified folder."
)
@click.option(
    "--filename-format",
    default="{date} {invoice_number} {desc}.pdf",
    help="Filename format to use when moving or copying processed PDFs."
    'Default: "{date} {invoice_number} {desc}.pdf"',
)
@click.option(
    "--template-folder",
    "-t",
    type=click.Path(exists=True),
    help="Folder containing invoice templates in yml file. Always adds built-in templates.",
)
@click.option(
    "--exclude-built-in-templates",
    is_flag=True,
    help="Ignore built-in templates.",
)
@click.argument(
    "input_files",
    type=click.File("wb"),
    # type=click.Path(exists=True),
    nargs=-1,
)
# @click.pass_context
@click.version_option()
def main(
    input_reader,
    output_format,
    output_date_format,
    output_name,
    debug,
    copy,
    move,
    filename_format,
    template_folder,
    exclude_built_in_templates,
    input_files,
):
    """Extract structured data from PDF files and save to CSV or JSON."""
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)

    input_module = input_mapping.get(input_reader)
    output_module = output_mapping[output_format]

    templates = []
    if template_folder:
        templates.extend(read_templates(os.path.abspath(template_folder)))
    if not exclude_built_in_templates:
        templates.extend(read_templates())

    output = []
    for f in input_files:
        try:  # Check if res is not None
            res = extract_data(f.name, templates=templates, input_module=input_module)
            if res:
                logger.info(res)
                output.append(res)

                if copy or move:  # Only perform copy/move operations if needed
                    # Create a deepcopy of res only if it's a dictionary
                    if not isinstance(res, dict):
                        kwargs = res.to_dict()  # Convert KeyValue to dict
                    else:
                        kwargs = deepcopy(res)
                    for key, value in kwargs.items():
                        if isinstance(value, list) and len(value) >= 1:
                            kwargs[key] = value[0]
                    for key, value in kwargs.items():
                        if isinstance(value, datetime.datetime):
                            kwargs[key] = value.strftime("%Y-%m-%d")
                    if copy:
                        filename = filename_format.format(**kwargs)
                        shutil.copyfile(f.name, join(copy, filename))
                    if move:
                        filename = filename_format.format(**kwargs)
                        shutil.move(f.name, join(move, filename))
        except Exception as e:
            logger.critical(
                "Invoice2data failed to process %s. \nError message: %s", f.name, e
            )
        finally:
            f.close()

    if output_module is not None:
        output_module.write_to_file(output, output_name, output_date_format)


if __name__ == "__main__":
    main(prog_name="invoice2data")  # pragma: no cover
