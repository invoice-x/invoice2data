import logging
from collections import OrderedDict
from pathlib import Path

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


def read_templates(folder: str = None):
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

    templatedirectory: Path = Path(folder)

    for yamlfile in sorted(templatedirectory.glob("**/*.yml")):
        try:
            template = ordered_load(yamlfile.read_text(encoding="utf-8"))
        except yaml.parser.ParserError as error:
            logger.warning(f"Failed to load {yamlfile.name} template:\n{error}")
            continue

        template["template_name"] = yamlfile.stem

        # Test if all required fields are in template
        if "keywords" not in template.keys():
            raise ValueError("Missing mandatory 'keywords' field.")

        # Convert keywords to list, if only one
        if not isinstance(template["keywords"], list):
            template["keywords"] = [template["keywords"]]

        # Set excluded_keywords as empty list, if not provided
        if "exclude_keywords" not in template.keys():
            template["exclude_keywords"] = []

        # Convert excluded_keywords to list, if only one
        if not isinstance(template["exclude_keywords"], list):
            template["exclude_keywords"] = [template["exclude_keywords"]]

        invoicetemplates.append(InvoiceTemplate(template))

    logger.info(f"Loaded {len(invoicetemplates)} templates from {folder}")

    return invoicetemplates
