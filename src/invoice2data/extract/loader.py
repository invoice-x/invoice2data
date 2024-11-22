"""This module abstracts templates for invoice providers.

Templates are initially read from .yml or .json files and then kept as class.
"""

import codecs
import json
import os
from logging import getLogger
from typing import Any
from typing import Callable
from typing import Dict
from typing import List


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


def ordered_load(stream: str, loader: Callable = json.loads) -> List[InvoiceTemplate]:
    """Loads a stream of JSON data.

    Args:
        stream (str): JSON data string.
        loader (Callable, optional): JSON loader function. Defaults to json.loads.

    Returns:
        List[InvoiceTemplate]: List of InvoiceTemplate objects.
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


def read_templates(folder: str = None) -> List[InvoiceTemplate]:
    """Load YAML templates from template folder. Return list of dicts.

    Use built-in templates if no folder is set.

    Args:
        folder (str, optional): User-defined folder where templates are stored.
                                If None, uses built-in templates.

    Returns:
        List[InvoiceTemplate]: List of InvoiceTemplate objects.

    Examples:
        >>> read_template("home/duskybomb/invoice-templates/")
        [InvoiceTemplate(...)]

        >>> my_template = InvoiceTemplate(...)
        >>> extract_data("invoice2data/test/pdfs/oyo.pdf", my_template, pdftotext)
        {...}
    """
    output = []
    if folder is None:
        folder = "./src/invoice2data/extract/templates"
    else:
        folder = os.path.abspath(folder)

    for path, _subdirs, files in os.walk(folder):
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


def prepare_template(tpl: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a template for use.

    Args:
        tpl (Dict[str, Any]): Template dictionary.

    Returns:
        Dict[str, Any]: Processed template dictionary.
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

    # Safely handle missing 'exclude_keywords'
    if "exclude_keywords" in tpl:
        tpl["exclude_keywords"] = (
            [tpl["exclude_keywords"]]
            if not isinstance(tpl["exclude_keywords"], list)
            else tpl["exclude_keywords"]
        )
    else:
        tpl["exclude_keywords"] = []  # Set to empty list if not present

    # Set priority if not provided
    tpl.setdefault("priority", 5)

    return tpl
