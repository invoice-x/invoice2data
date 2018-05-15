"""
This module abstracts templates for invoice providers.

Templates are initially read from .yml files and then kept as class.
"""

import os
import yaml
import pkg_resources
from collections import OrderedDict
import logging as logger
from .invoice_template import InvoiceTemplate
import codecs
import chardet

# borrowed from http://stackoverflow.com/a/21912744
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """load mappings and ordered mappings

    loader to load mappings and ordered mappings into the Python 2.7+ OrderedDict type,
    instead of the vanilla dict and the list of pairs it currently uses.
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)


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
    InvoiceTemplate([('issuer', 'OYO'), ('fields', OrderedDict([('amount', 'GrandTotalRs(\\d+)'),
    ('date', 'Date:(\\d{1,2}\\/\\d{1,2}\\/\\d{1,4})'), ('invoice_number', '([A-Z0-9]+)CashatHotel')])),
    ('keywords', ['OYO', 'Oravel', 'Stays']), ('options', OrderedDict([('currency', 'INR'), ('decimal_separator', '.'),
    ('remove_whitespace', True)])), ('template_name', 'com.oyo.invoice.yml')])

    After reading the template you can use the result as an instance of `InvoiceTemplate` to extract fields from
    `extract_data()`

    >>> my_template = InvoiceTemplate([('issuer', 'OYO'), ('fields', OrderedDict([('amount', 'GrandTotalRs(\\d+)'),
    ('date', 'Date:(\\d{1,2}\\/\\d{1,2}\\/\\d{1,4})'), ('invoice_number', '([A-Z0-9]+)CashatHotel')])),
    ('keywords', ['OYO', 'Oravel', 'Stays']), ('options', OrderedDict([('currency', 'INR'), ('decimal_separator', '.'),
    ('remove_whitespace', True)])), ('template_name', 'com.oyo.invoice.yml')])
    >>> extract_data("invoice2data/test/pdfs/oyo.pdf", my_template, pdftotext)
    {'issuer': 'OYO', 'amount': 1939.0, 'date': datetime.datetime(2017, 12, 31, 0, 0), 'invoice_number': 'IBZY2087',
     'currency': 'INR', 'desc': 'Invoice IBZY2087 from OYO'}

    """

    output = []

    if folder is None:
        folder = pkg_resources.resource_filename(__name__, 'templates')

    for path, subdirs, files in os.walk(folder):
        for name in sorted(files):
            if name.endswith('.yml'):
                with codecs.open(os.path.join(path, name), encoding=chardet.detect(open(os.path.join(path, name), 'rb').read())['encoding']) as template_file:
                    tpl = ordered_load(template_file.read())
                tpl['template_name'] = name

                # Test if all required fields are in template:
                assert 'keywords' in tpl.keys(), 'Missing keywords field.'
                required_fields = ['date', 'amount', 'invoice_number']
                assert len(set(required_fields).intersection(tpl['fields'].keys())) == len(required_fields), \
                    'Missing required key in template {} {}. Found {}'.format(name, path, tpl['fields'].keys())

                # Keywords as list, if only one.
                if type(tpl['keywords']) is not list:
                    tpl['keywords'] = [tpl['keywords']]

                output.append(InvoiceTemplate(tpl))
    return output
