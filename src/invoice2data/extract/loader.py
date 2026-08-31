"""This module abstracts templates for invoice providers.

Templates are initially read from .yml or .json files and then kept as class.
"""

import contextlib
import json
import os
from collections.abc import Callable
from functools import lru_cache
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


def _folder_signature(folder: str) -> tuple[tuple[str, int], ...]:
    """Cheap fingerprint of a template folder: sorted ``(path, mtime_ns)`` pairs.

    Cheap enough (stat-only, no file reads) to compute on every call, sensitive
    enough that any file add/remove/rewrite busts the memoization cache below.

    Args:
        folder (str): Absolute path to the template folder.

    Returns:
        tuple[tuple[str, int], ...]: Immutable, hashable signature.
    """
    entries: list[tuple[str, int]] = []
    for path, _subdirs, files in os.walk(folder):
        for name in files:
            full = Path(path) / name
            with contextlib.suppress(OSError):
                # File vanished between walk() and stat() -- skip; signature
                # will differ on the next call and cache re-populates.
                entries.append((str(full), full.stat().st_mtime_ns))
    entries.sort()
    return tuple(entries)


@lru_cache(maxsize=8)
def _read_templates_cached(
    folder: str, _signature: tuple[tuple[str, int], ...]
) -> tuple[InvoiceTemplate, ...]:
    """Actual template-loading work; keyed by folder + folder-signature.

    Returns an immutable tuple so a caller mutating the sequence can't corrupt
    a peer's cached view; :func:`read_templates` converts to a fresh ``list``
    on the way out.
    """
    output: list[InvoiceTemplate] = []
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
    return tuple(output)


def read_templates(folder: str | None = None) -> list[InvoiceTemplate]:
    """Load YAML templates from template folder. Return list of dicts.

    Use built-in templates if no folder is set.

    Memoized: repeat calls for an unchanged folder skip the disk read and
    YAML parse. The cache is keyed by folder path + a cheap ``(path, mtime)``
    signature, so any file add/remove/rewrite invalidates it automatically.
    Callers get a fresh list so mutating the returned sequence is safe.

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
    if folder is None:
        folder = str(Path(__file__).parent / "templates")
    else:
        folder = str(Path(folder).resolve())
    return list(_read_templates_cached(folder, _folder_signature(folder)))


def _prepare_match_selector(tpl: dict[str, Any]) -> bool:
    """Normalize an explicit ``match`` selector into legacy internal keys."""
    match = tpl.get("match")
    if match is None:
        return True
    if not isinstance(match, dict):
        logger.warning(
            "Failed to load template %s. 'match' must be a mapping.",
            tpl.get("template_name", "<stream>"),
        )
        return False
    if any(key in tpl for key in ("keywords", "exclude_keywords", "pages")):
        logger.warning(
            "Failed to load template %s. Put keywords, exclude_keywords and "
            "pages inside 'match', not alongside it.",
            tpl.get("template_name", "<stream>"),
        )
        return False
    if "keywords" not in match:
        logger.warning(
            "Failed to load template %s. 'match' is missing mandatory 'keywords'.",
            tpl.get("template_name", "<stream>"),
        )
        return False
    # Keep the established internal representation. The nested selector is
    # retained for its page scope while InvoiceTemplate continues to expose
    # keywords at the top level to existing callers and plugins.
    tpl["keywords"] = match["keywords"]
    if "exclude_keywords" in match:
        tpl["exclude_keywords"] = match["exclude_keywords"]
    return True


def prepare_template(tpl: dict[str, Any]) -> dict[str, Any] | None:
    """Prepare a template for use.

    Args:
        tpl (dict[str, Any]): Template dictionary.

    Returns:
        dict[str, Any] | None: Processed template dictionary.
    """
    if not _prepare_match_selector(tpl):
        return None

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

    # Issue #743: catch the YAML-quoting trap where a keyword ending in ``:``
    # is parsed as an inline mapping ({'invoice id': None}) instead of a
    # string. Left unchecked, ``matches_input`` later crashes with
    # ``TypeError: 'in <string>' requires string as left operand, not dict``.
    # Drop the offending template and log a hint that the value must be
    # quoted in YAML.
    for key in ("keywords", "exclude_keywords"):
        for value in tpl[key]:
            if not isinstance(value, str):
                logger.warning(
                    "Failed to load template %s. `%s` entry must be a string, "
                    "got %s (%r). Hint: a YAML keyword ending in `:` needs to "
                    "be quoted, e.g. `- 'invoice id:'`.",
                    tpl.get("template_name", "<stream>"),
                    key,
                    type(value).__name__,
                    value,
                )
                return None

    # Set priority if not provided
    tpl.setdefault("priority", 5)

    return tpl
