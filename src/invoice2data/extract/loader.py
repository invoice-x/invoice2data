"""This module abstracts templates for invoice providers.

Templates are initially read from .yml or .json files and then kept as class.
"""

import json
import os
from collections.abc import Callable
from logging import getLogger
from typing import Any


try:
    from yaml import CSafeLoader as SafeLoader
    from yaml import YAMLError
    from yaml import load
except ImportError:  # pragma: no cover
    from yaml import SafeLoader  # type: ignore[import-untyped]
    from yaml import YAMLError
    from yaml import load

from .invoice_template import InvoiceTemplate  # type: ignore[unused-ignore]


logger = getLogger(__name__)


def ordered_load(
    stream: str, loader: Callable[[str], Any] = json.loads
) -> list[InvoiceTemplate]:
    """Loads a stream of JSON data.

    Args:
        stream (str): JSON data string.
        loader (Callable[[str], Any], optional): JSON loader function. Defaults to json.loads.

    Returns:
        list[InvoiceTemplate]: List of InvoiceTemplate objects.
    """
    output = []

    try:
        tpl_stream = json.loads(stream)
    except ValueError as error:
        logger.warning("JSON Loader Failed to load template stream\n%s", error)
        return []

    # Always pre-process template to remain backwards compatible
    for tpl in tpl_stream:
        tpl = prepare_template(tpl)
        if tpl:
            output.append(InvoiceTemplate(tpl))

    return output


def read_templates(folder: str | None = None) -> list[InvoiceTemplate]:
    """Load YAML templates from template folder. Return list of dicts.

    Use built-in templates if no folder is set.

    Args:
        folder (str | None): User-defined folder where templates are stored.
                                If None, uses built-in templates.

    Returns:
        list[InvoiceTemplate]: List of InvoiceTemplate objects.

    Examples:
        >>> templates = read_templates("./src/invoice2data/extract/templates/au")
        >>> len(templates)  # Check the number of loaded templates
        2
        >>> templates[0]['template_name']  # Check the name of the first template
                'au.com.opal.yml'
    """
    output = []
    if folder is None:
        folder = os.path.join(os.path.dirname(__file__), "templates")
    else:
        folder = os.path.abspath(folder)

    for path, _subdirs, files in os.walk(folder):
        for name in sorted(files):
            with open(os.path.join(path, name), encoding="utf-8") as template_file:
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


def prepare_template(tpl: dict[str, Any]) -> dict[str, Any] | None:
    """Prepare a template for use.

    Args:
        tpl (dict[str, Any]): Template dictionary.

    Returns:
        dict[str, Any] | None: Processed template dictionary.
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
