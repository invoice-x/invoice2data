"""
This module abstracts templates for invoice providers.

Templates are initially read from .yml files and then kept as class.
"""

import os
import yaml
import pkg_resources
from collections import OrderedDict
import logging as logger
from .base_template import BaseInvoiceTemplate
from .line_template import LineInvoiceTemplate

# borrowed from http://stackoverflow.com/a/21912744
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):

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
    """

    output = []

    if folder is None:
        folder = pkg_resources.resource_filename('extract', 'templates')

    for path, subdirs, files in os.walk(folder):
        for name in sorted(files):
            if name.endswith('.yml'):
                with open(os.path.join(path, name)) as template_file:
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

                if 'lines' in tpl:
                    assert 'start' in tpl['lines'], 'Lines start regex missing'
                    assert 'end' in tpl['lines'], 'Lines end regex missing'
                    assert 'line' in tpl['lines'], 'Line regex missing'
                    output.append(LineInvoiceTemplate(tpl))
                else:
                    output.append(BaseInvoiceTemplate(tpl))
    return output
