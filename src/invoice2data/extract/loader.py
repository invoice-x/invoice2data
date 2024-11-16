"""This module abstracts templates for invoice providers.

Templates are initially read from .yml or .json files and then kept as class.
"""

import codecs
import json
import os
from importlib.resources import files
from logging import getLogger


try:
    from yaml import CSafeLoader as SafeLoader
    from yaml import YAMLError
    from yaml import load
except ImportError:  # pragma: no cover
    from yaml import SafeLoader
    from yaml import YAMLError
    from yaml import load

from .invoice_template import InvoiceTemplate


logger = getLogger(__name__)


def ordered_load(stream, loader=json.loads):
    """Loads a stream of JSON data.

    Args:
        stream (str): JSON data string.
        loader (callable, optional): JSON loader function. Defaults to json.loads.

    Returns:
        list: List of InvoiceTemplate objects.
    """
    output = []

    try:
        tpl_stream = json.loads(stream)
    except ValueError as error:
        logger.warning("JSON Loader Failed to load template stream\n%s", error)
        return

    # Always pre-process template to remain backwards compatible
    for tpl in tpl_stream:
        tpl = prepare_template(tpl)
        if tpl:
            output.append(InvoiceTemplate(tpl))

    return output


def read_templates(folder=None):
    """Load YAML templates from template folder. Return list of dicts.

    Use built-in templates if no folder is set.

    Args:
        folder (str, optional): User-defined folder where templates are stored.
                                If None, uses built-in templates.

    Returns:
        list: List of InvoiceTemplate objects.

    Examples:
        >>> read_template("home/duskybomb/invoice-templates/")
        [InvoiceTemplate(...)]

        >>> my_template = InvoiceTemplate(...)
        >>> extract_data("invoice2data/test/pdfs/oyo.pdf", my_template, pdftotext)
        {...}
    """
    output = []

    if folder is None:
        folder = files(__package__).joinpath("templates")  # Use importlib.resources
    else:
        folder = os.path.abspath(folder)

    for filename in os.listdir(folder):
        if not filename.endswith((".yaml", ".yml", ".json")):
            continue

        filepath = os.path.join(folder, filename)
        with codecs.open(filepath, encoding="utf-8") as template_file:
            try:
                if filename.endswith((".yaml", ".yml")):
                    tpl = load(template_file.read(), Loader=SafeLoader)
                elif filename.endswith(".json"):
                    tpl = json.loads(template_file.read())
            except (YAMLError, ValueError) as error:
                logger.warning("Failed to load %s template:\n%s", filename, error)
                continue

        tpl["template_name"] = filename
        tpl = prepare_template(tpl)

        if tpl:
            output.append(InvoiceTemplate(tpl))

    logger.info("Loaded %d templates from %s", len(output), folder)
    return output


def prepare_template(tpl):
    """Prepare a template for use.

    Args:
        tpl (dict): Template dictionary.

    Returns:
        dict: Processed template dictionary.
    """
    # Test if all required fields are in template
    if "keywords" not in tpl:
        logger.warning(
            "Failed to load template %s. Missing mandatory 'keywords' field.",
            tpl["template_name"],
        )
        return None

    # Convert keywords and exclude_keywords to lists if they are not already
    tpl["keywords"] = (
        [tpl["keywords"]] if not isinstance(tpl["keywords"], list) else tpl["keywords"]
    )
    tpl["exclude_keywords"] = (
        [tpl["exclude_keywords"]]
        if not isinstance(tpl["exclude_keywords"], list)
        else tpl["exclude_keywords"]
    )

    # Set priority if not provided
    tpl.setdefault("priority", 5)

    return tpl
