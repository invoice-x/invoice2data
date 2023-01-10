import logging
import os
from collections import OrderedDict

import chardet
import pkg_resources
import yaml

from .invoice_template import InvoiceTemplate

logger = logging.getLogger(__name__)

logging.getLogger("chardet").setLevel(logging.WARNING)


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

    templates = []

    if folder is None:
        folder = pkg_resources.resource_filename(__name__, "templates")

    for templatefile, templatename in get_templatefiles(folder).items():
        try:
            encoding = detect_template_encoding(templatefile)
            template = load_template(templatefile, encoding)
        except yaml.parser.ParserError as error:
            logger.warning(
                "Failed to load {} template:\n{}".format(templatename, error)
            )
            continue

        invoicetemplate = optimise_template(template, templatename)
        templates.append(invoicetemplate)

    logger.info("Loaded {} templates from {}".format(len(templates), folder))

    return templates


def detect_template_encoding(templatefile: str) -> str:
    with open(templatefile, "rb") as file:
        detection_result = chardet.detect(file.read())
        detected_encoding = detection_result["encoding"]

    template = load_template(templatefile, detected_encoding)
    template_options = template.get("options", {})
    template_encoding = template_options.get("encoding", detected_encoding)

    return template_encoding


def get_templatefiles(directory: str):
    templatefiles = {}

    for path, _, files in os.walk(directory):
        for filename in sorted(files):
            if filename.endswith(".yml"):
                filepath = os.path.join(path, filename)
                templatefiles[filepath] = filename

    return templatefiles


def load_template(templatefile: str, encoding: str) -> OrderedDict:
    with open(templatefile, "r", encoding=encoding) as file:
        return ordered_load(file.read())


def optimise_template(template: OrderedDict, templatename: str) -> InvoiceTemplate:
    template["template_name"] = templatename

    # Ensure that all required fields are in template
    try:
        template["keywords"]
    except KeyError:
        raise AttributeError("Missing keywords field in '{}'".format(templatename))

    # Keywords as list, if only one.
    if not isinstance(template["keywords"], list):
        template["keywords"] = [template["keywords"]]

    # Define excluded_keywords as empty list if not provided
    # Convert to list if only one provided
    if "exclude_keywords" not in template.keys():
        template["exclude_keywords"] = []

    if not isinstance(template["exclude_keywords"], list):
        template["exclude_keywords"] = [template["exclude_keywords"]]

    return InvoiceTemplate(template)
