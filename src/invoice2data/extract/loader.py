import codecs
import logging
import os
from collections import OrderedDict

import pkg_resources
import yaml

from .invoice_template import InvoiceTemplate

logger = logging.getLogger(__name__)


def ordered_load(stream):
    # Simplified version of http://stackoverflow.com/a/21912744
    class OrderedLoader(yaml.Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )

    return yaml.load(stream, OrderedLoader)


def read_templates(folder=None):
    """
    Load yaml templates from template folder. Use built-in templates if no folder is set.

    Parameters
    ----------
    folder : str

    Returns
    -------
    invoicetemplates : list of `InvoiceTemplate`
    """

    invoicetemplates = []

    if folder is None:
        folder = pkg_resources.resource_filename(__name__, "templates")

    for path, _, files in os.walk(folder):
        for name in sorted(files):
            if name.endswith(".yml"):
                with codecs.open(
                    os.path.join(path, name), encoding="utf-8"
                ) as template_file:
                    try:
                        template = ordered_load(template_file.read())
                    except yaml.parser.ParserError as error:
                        logger.warning("Failed to load %s template:\n%s", name, error)
                        continue
                template["template_name"] = name

                # Test if all required fields are in template:
                assert "keywords" in template.keys(), "Missing keywords field."

                # Keywords as list, if only one.
                if type(template["keywords"]) is not list:
                    template["keywords"] = [template["keywords"]]

                # Define excluded_keywords as empty list if not provided
                # Convert to list if only one provided
                if "exclude_keywords" not in template.keys():
                    template["exclude_keywords"] = []
                elif type(template["exclude_keywords"]) is not list:
                    template["exclude_keywords"] = [template["exclude_keywords"]]

                invoicetemplates.append(InvoiceTemplate(template))

    logger.info("Loaded %d templates from %s", len(invoicetemplates), folder)

    return invoicetemplates
