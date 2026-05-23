"""This module abstracts templates for invoice providers.

Templates are initially read from .yml or .json files and then kept as class.
"""

import json
import os
from collections.abc import Callable
from logging import getLogger
from pathlib import Path
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
    """Parse templates from an in-memory string instead of from disk.

    Useful when templates live outside the filesystem (e.g. a database column or
    an API payload): ``extract_data(file, templates=ordered_load(db_text))``. For
    YAML data pass ``loader=yaml.safe_load``.

    Args:
        stream (str): Serialized templates -- a JSON (default) or YAML array of
            template mappings.
        loader (Callable[[str], Any], optional): Callable turning ``stream`` into
            a list of template dicts. Defaults to ``json.loads``; pass
            ``yaml.safe_load`` for YAML.

    Returns:
        list[InvoiceTemplate]: Parsed, prepared templates (empty list on a parse
            error, which is logged).
    """
    try:
        tpl_stream = loader(stream)
    except (ValueError, YAMLError) as error:
        logger.warning("Failed to load template stream\n%s", error)
        return []

    output = []
    # Always pre-process templates to remain backwards compatible.
    for raw_tpl in tpl_stream:
        tpl = prepare_template(raw_tpl)
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
        folder = str(Path(__file__).parent / "templates")
    else:
        folder = str(Path(folder).resolve())

    for path, _subdirs, files in os.walk(folder):
        for name in sorted(files):
            with (Path(path) / name).open(encoding="utf-8") as template_file:
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
            tpl.get("template_name", "<stream>"),
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
