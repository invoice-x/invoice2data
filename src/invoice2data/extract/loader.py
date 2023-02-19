import codecs
import logging
import os
from collections import OrderedDict

import pkg_resources
import yaml

from .invoice_template import InvoiceTemplate

logger = logging.getLogger(__name__)


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
    output : list of `InvoiceTemplate`
    """

    output = []

    if folder is None:
        folder = pkg_resources.resource_filename(__name__, "templates")

    for path, subdirs, files in os.walk(folder):
        for name in sorted(files):
            if name.endswith(".yml"):
                with codecs.open(
                    os.path.join(path, name), encoding="utf-8"
                ) as template_file:
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

                output.append(InvoiceTemplate(tpl))

    logger.info("Loaded %d templates from %s", len(output), folder)

    return output
