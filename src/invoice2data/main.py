#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import copy
import datetime
import shutil
import os
from os.path import join
import logging

from .input import pdftotext
from .input import pdfminer_wrapper
from .input import pdfplumber
from .input import tesseract
from .input import gvision
from .input import text
from .input import ocrmypdf

from invoice2data.extract.loader import read_templates

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

    FORMAT = \
        "%(prefix)s%(levelname)s:%(suffix)s%(name)s:%(prefix)s %(message)s%(suffix)s"

    LOG_LEVEL_COLOR = {
        "DEBUG": {"prefix": "", "suffix": Color.END},
        "INFO": {"prefix": Color.BLUE, "suffix": Color.END},
        "WARNING": {"prefix": Color.YELLOW_BACK, "suffix": Color.END},
        "ERROR": {"prefix": Color.RED_BACK, "suffix": Color.END},
        "CRITICAL": {"prefix": Color.BOLD_RED, "suffix": Color.END},
    }

    def format(self, record):
        """Format log records with a default prefix and suffix
           to terminal color codes that corresponds to the log level name."""

        if not hasattr(record, "prefix"):
            record.prefix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get("prefix")

        if not hasattr(record, "suffix"):
            record.suffix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get("suffix")

        formatter = logging.Formatter(self.FORMAT)
        return formatter.format(record)


stream_handler = logging.StreamHandler()
stream_handler.setFormatter(ColorLogFormatter())
logger.propagate = False

if not logger.handlers:
    logger.addHandler(stream_handler)


def extract_data(invoicefile, templates=None, input_module=None):
    """Extracts structured data from PDF/image invoices.

    This function uses the text extracted from a PDF file or image and
    pre-defined regex templates to find structured data.

    Reads template if no template assigned
    Required fields are matches from templates

    Parameters
    ----------
    invoicefile : str
        path of electronic invoice file in PDF,JPEG,PNG (example: "/home/duskybomb/pdf/invoice.pdf")
    templates : list of instances of class `InvoiceTemplate`, optional
        Templates are loaded using `read_template` function in `loader.py`
    input_module : {'pdftotext', 'pdfminer', 'tesseract', 'text'}, optional
        library to be used to extract text from given `invoicefile`,

    Returns
    -------
    dict or False
        extracted and matched fields or False if no template matches

    Notes
    -----
    Import required `input_module` when using invoice2data as a library

    See Also
    --------
    read_template : Function where templates are loaded
    InvoiceTemplate : Class representing single template files that live as .yml files on the disk

    Examples
    --------
    When using `invoice2data` as an library

    >>> from invoice2data.input import pdftotext
    >>> extract_data("invoice2data/test/pdfs/oyo.pdf", None, pdftotext)
    {'issuer': 'OYO', 'amount': 1939.0, 'date': datetime.datetime(2017, 12, 31, 0, 0), 'invoice_number': 'IBZY2087',
     'currency': 'INR', 'desc': 'Invoice IBZY2087 from OYO'}

    """

    if input_module is None:
        if invoicefile.lower().endswith('.txt'):
            input_module = text
        else:
            input_module = pdftotext

    extracted_str = input_module.to_text(invoicefile)
    if not isinstance(extracted_str, str) or not extracted_str.strip():
        logger.error("Failed to extract text from %s using %s", invoicefile, input_module.__name__)
        return False

    logger.debug("START pdftotext result ===========================\n%s"
                 , extracted_str)
    logger.debug("END pdftotext result =============================")

    if templates is None:
        templates = read_templates()
    templates_matched = filter(lambda t: t.matches_input(extracted_str), templates)
    templates_matched = sorted(templates_matched, key=lambda k: k['priority'], reverse=True)
    if not templates_matched:
        if ocrmypdf.have_ocrmypdf() and input_module is not ocrmypdf:
            logger.debug("Text extraction failed, falling back to ocrmypdf")
            extracted_str, invoicefile, templates_matched = extract_data_fallback_ocrmypdf(invoicefile, templates)
            if not templates_matched:
                logger.error("No template for %s", invoicefile)
                return False
        else:
            logger.error("No template for %s", invoicefile)
            return False

    t = templates_matched[0]
    logger.info("Using %s template", t["template_name"])
    optimized_str = t.prepare_input(extracted_str)
    return t.extract(optimized_str, invoicefile, input_module)


def extract_data_fallback_ocrmypdf(invoicefile, templates):
    logger.debug("Text extraction failed, falling back to ocrmypdf")
    extracted_str = ocrmypdf.to_text(invoicefile)
    templates_matched = filter(lambda t: t.matches_input(extracted_str), templates)
    templates_matched = sorted(templates_matched, key=lambda k: k['priority'], reverse=True)
    return extracted_str, invoicefile, templates_matched


def create_parser():
    """Returns argument parser """

    parser = argparse.ArgumentParser(
        description="Extract structured data from PDF files and save to CSV or JSON."
    )

    parser.add_argument(
        "--input-reader",
        choices=input_mapping.keys(),
        help="Choose text extraction function. Default: auto-detect between text & pdftotext",
    )

    parser.add_argument(
        "--output-format",
        choices=output_mapping.keys(),
        default="none",
        help="Choose output format. Default: none",
    )

    parser.add_argument(
        "--output-date-format",
        dest="output_date_format",
        default="%Y-%m-%d",
        help="Choose output date format. Default: %%Y-%%m-%%d (ISO 8601 Date)",
    )

    parser.add_argument(
        "--output-name",
        "-o",
        dest="output_name",
        default="invoices-output",
        help="Custom name for output file. Extension is added based on chosen format.",
    )

    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Enable debug information."
    )

    parser.add_argument(
        "--copy",
        "-c",
        dest="copy",
        help="Copy and rename processed PDFs to specified folder.",
    )

    parser.add_argument(
        "--move",
        "-m",
        dest="move",
        help="Move and rename processed PDFs to specified folder.",
    )

    parser.add_argument(
        "--filename-format",
        dest="filename",
        default="{date} {invoice_number} {desc}.pdf",
        help="Filename format to use when moving or copying processed PDFs."
        'Default: "{date} {invoice_number} {desc}.pdf"',
    )

    parser.add_argument(
        "--template-folder",
        "-t",
        dest="template_folder",
        help="Folder containing invoice templates in yml file. Always adds built-in templates.",
    )

    parser.add_argument(
        "--exclude-built-in-templates",
        dest="exclude_built_in_templates",
        default=False,
        help="Ignore built-in templates.",
        action="store_true",
    )

    parser.add_argument(
        "input_files",
        type=argparse.FileType("r"),
        nargs="+",
        help="File or directory to analyze.",
    )

    return parser


def main(args=None):
    """Take folder or single file and analyze each."""

    if args is None:
        parser = create_parser()
        args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)

    input_module = input_mapping[args.input_reader] if args.input_reader is not None else None
    output_module = output_mapping[args.output_format]

    templates = []

    # Load templates from external folder if set.

    if args.template_folder:
        templates += read_templates(os.path.abspath(args.template_folder))

    # Load internal templates, if not disabled.

    if not args.exclude_built_in_templates:
        templates += read_templates()
    output = []
    for f in args.input_files:
        try:
            res = extract_data(f.name, templates=templates, input_module=input_module)
            if res:
                logger.info(res)
                output.append(res)

                kwargs = copy.deepcopy(res)
                for key, value in kwargs.items():
                    if type(value) is list and len(value) >= 1:
                        kwargs[key] = value[0]
                for key, value in kwargs.items():
                    if type(value) is datetime.datetime:
                        kwargs[key] = value.strftime('%Y-%m-%d')
                if args.copy:
                    filename = args.filename.format(**kwargs)
                    shutil.copyfile(f.name, join(args.copy, filename))
                if args.move:
                    filename = args.filename.format(**kwargs)
                    shutil.move(f.name, join(args.move, filename))
            f.close()
        except Exception as e:
            logger.critical("Invoice2data failed to process %s. \nError message: %s", f.name, e)
            continue

    if output_module is not None:
        output_module.write_to_file(output, args.output_name, args.output_date_format)


if __name__ == "__main__":
    main()
