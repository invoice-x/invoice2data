"""
This module abstracts templates for invoice providers.

Templates are initially read from .yml files and then kept as class.
"""

import os
import yaml
import pkg_resources
import logging
from .invoice_template import InvoiceTemplate
import codecs

logger = logging.getLogger(__name__)


def read_templates(folder=None):
    """
    Load yaml templates from template folder. Return list of dicts.

    Use built-in templates if no folder is set.

    Parameters
    ----------
    folder : str
        user defined folder where they stores their files, if None uses built-in templates

    Returns
    -------
    output : Instance of `InvoiceTemplate`
        template which match based on keywords

    Examples
    --------

    >>> read_template("home/duskybomb/invoice-templates/")
    InvoiceTemplate([('issuer', 'OYO'), ('fields', {'amount': 'Grand Total\\s+Rs (\\d+)',
    'date': 'Date:\\s(\\d{1,2}\\/\\d{1,2}\\/\\d{1,4})', 'invoice_number': '([A-Z0-9]+)\\s+Cash at Hotel'}),
    ('keywords', ['OYO', 'Oravel', 'Stays']), ('options', {'currency': 'INR', 'decimal_separator': '.'}),
    ('template_name', 'com.oyo.invoice.yml'), ('exclude_keywords', [])])

    After reading the template you can use the result as an instance of `InvoiceTemplate` to extract fields from
    `extract_data()`

    >>> my_template = InvoiceTemplate([('issuer', 'OYO'), ('fields', {'amount': 'Grand Total\\s+Rs (\\d+)',
    'date': 'Date:\\s(\\d{1,2}\\/\\d{1,2}\\/\\d{1,4})', 'invoice_number': '([A-Z0-9]+)\\s+Cash at Hotel'}),
    ('keywords', ['OYO', 'Oravel', 'Stays']), ('options', {'currency': 'INR', 'decimal_separator': '.'}),
    ('template_name', 'com.oyo.invoice.yml'), ('exclude_keywords', [])])
    >>> extract_data("invoice2data/test/pdfs/oyo.pdf", my_template, pdftotext)
    {'issuer': 'OYO', 'amount': 1939.0, 'date': datetime.datetime(2017, 12, 31, 0, 0), 'invoice_number': 'IBZY2087',
    'currency': 'INR', 'desc': 'Invoice IBZY2087 from OYO'}

    """

    output = []

    if folder is None:
        folder = pkg_resources.resource_filename(__name__, "templates")

    for path, subdirs, files in os.walk(folder):
        for name in sorted(files):
            with codecs.open(
                os.path.join(path, name), encoding="utf-8"
            ) as template_file:
                if name.endswith(".yml"):
                    try:
                        tpl = ordered_load(template_file.read())
                    except yaml.parser.ParserError as error:
                        logger.warning("Failed to load %s template:\n%s", name, error)
                        continue

            tpl["template_name"] = name

            # Test if all required fields are in template:
            assert "keywords" in tpl.keys(), "Missing keywords field."

            # Keywords as list, if only one.
            if type(tpl["keywords"]) is not list:
                tpl["keywords"] = [tpl["keywords"]]

            # Define excluded_keywords as empty list if not provided
            # Convert to list if only one provided
            if "exclude_keywords" not in tpl.keys():
                tpl["exclude_keywords"] = []
            elif type(tpl["exclude_keywords"]) is not list:
                tpl["exclude_keywords"] = [tpl["exclude_keywords"]]

            if 'priority' not in tpl.keys():
                tpl['priority'] = 5

            output.append(InvoiceTemplate(tpl))

    logger.info("Loaded %d templates from %s", len(output), folder)

    return output
