"""
This module abstracts templates for invoice providers.

Templates are initially read from .yml or .json files and then kept as class.
"""

import os
import json

try:
    from yaml import load, YAMLError, CSafeLoader as SafeLoader
except ImportError:  # pragma: no cover
    from yaml import load, SafeLoader, YAMLError
import pkg_resources

from logging import getLogger
from .invoice_template import InvoiceTemplate
import codecs

logger = getLogger(__name__)


def ordered_load(stream, Loader=json.loads):
    """loads a stream of json data"""

    output = []

    try:
        tpl_stream = json.loads(stream)
    except ValueError as error:
        logger.warning("json Loader Failed to load template stream\n%s", error)
        return
    # always pre-process template to remain backwards compatability
    for tpl in tpl_stream:
        tpl = prepare_template(tpl)
        if tpl:
            output.append(InvoiceTemplate(tpl))

    return output


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
                if name.endswith((".yaml", ".yml")):
                    try:
                        tpl = load(template_file.read(), Loader=SafeLoader)
                    except YAMLError as error:
                        logger.warning("Failed to load %s template:\n%s", name, error)
                        continue
                elif name.endswith(".json"):
                    try:
                        tpl = json.loads(template_file.read())
                    except ValueError as error:
                        logger.warning(
                            "json Loader Failed to load %s template:\n%s", name, error
                        )
                        continue
                else:
                    continue
            tpl["template_name"] = name
            tpl = prepare_template(tpl)

            if tpl:
                output.append(InvoiceTemplate(tpl))

    logger.info("Loaded %d templates from %s", len(output), folder)
    return output


def prepare_template(tpl):
    # Test if all required fields are in template
    if "keywords" not in tpl.keys():
        logger.warning(
            "Failed to load template %s Missing mandatory 'keywords' field.",
            tpl["template_name"],
        )
        return None

    # Convert keywords to list, if only one
    if not isinstance(tpl["keywords"], list):
        tpl["keywords"] = [tpl["keywords"]]

    # Set excluded_keywords as empty list, if not provided
    if "exclude_keywords" not in tpl.keys():
        tpl["exclude_keywords"] = []

    # Convert excluded_keywords to list, if only one
    if not isinstance(tpl["exclude_keywords"], list):
        tpl["exclude_keywords"] = [tpl["exclude_keywords"]]

    if "priority" not in tpl.keys():
        tpl["priority"] = 5
    return tpl
