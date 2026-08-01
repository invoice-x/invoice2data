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


# Public API of this module (keeps the imported InvoiceTemplate out of the
# generated API docs, where it has its own dedicated entry).
__all__ = ["ordered_load", "prepare_template", "read_templates"]

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

    # Guard against payloads that parse successfully but are not a list of
    # templates (e.g. `json.loads("0")` returns an int, `yaml.safe_load("~")`
    # returns None). Without this, `for raw_tpl in tpl_stream` blew up with
    # a TypeError before reaching `prepare_template`.
    if not isinstance(tpl_stream, list):
        logger.warning(
            "Template stream must be a list of mappings, got %s; ignoring",
            type(tpl_stream).__name__,
        )
        return []

    output = []
    # Always pre-process templates to remain backwards compatible.
    for raw_tpl in tpl_stream:
        if not isinstance(raw_tpl, dict):
            logger.warning(
                "Template stream entry must be a mapping, got %s; skipping",
                type(raw_tpl).__name__,
            )
            continue
        tpl = prepare_template(raw_tpl)
        if tpl:
            output.append(InvoiceTemplate(tpl))

    return output


def _load_template_file(path: Path) -> Any:
    """Read + parse a single template file, or return ``None`` on any issue.

    Extracted from :func:`read_templates` to keep it under ruff's C901
    complexity ceiling. Handles the three ways a template file can be
    unusable -- unknown extension, parser error, empty/non-mapping content --
    with a warning per case so template authors can see what got dropped.

    Args:
        path (Path): Full path to the template file.

    Returns:
        Any: The parsed mapping, or ``None`` if the file was skipped.
    """
    name = path.name
    if name.endswith((".yaml", ".yml")):
        try:
            with path.open(encoding="utf-8") as f:
                tpl = load(f.read(), Loader=SafeLoader)
        except YAMLError as error:
            logger.warning("Failed to load %s template:\n%s", name, error)
            return None
    elif name.endswith(".json"):
        try:
            with path.open(encoding="utf-8") as f:
                tpl = json.loads(f.read())
        except ValueError as error:
            logger.warning("json Loader Failed to load %s template:\n%s", name, error)
            return None
    else:
        return None
    if tpl is None:
        logger.warning("Skipping empty template: %s", name)
        return None
    if not isinstance(tpl, dict):
        # `yaml.safe_load("0")` returns int, `yaml.safe_load("[]")` returns a
        # list, etc. Only mappings are valid templates.
        logger.warning(
            "Skipping %s: template must be a mapping, got %s",
            name,
            type(tpl).__name__,
        )
        return None
    return tpl


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
            tpl = _load_template_file(Path(path) / name)
            if not isinstance(tpl, dict):
                # `_load_template_file` returned None for parse errors, empty
                # files, or non-mapping content -- all logged there.
                logger.debug(
                    "Skipping %s: template must be a mapping, got %s",
                    name,
                    type(tpl).__name__,
                )
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
