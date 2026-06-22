"""Excalibur → invoice2data template converter.

Excalibur (`camelot-dev/excalibur`) is Camelot's visual table-region selector.
Once the user has drawn the table areas / column splits in the web UI and saved
a *rule*, Excalibur stores the configuration as a JSON ``rule_options`` blob
(top-level ``flavor`` + a per-page ``pages`` map, both consumed as kwargs by
``camelot.read_pdf``).

This module turns that blob into the ``camelot:`` block of an invoice2data
template, so a maintainer can author a table-heavy template visually instead of
hand-tuning coordinates.

Round-trip semantics mirror Excalibur's ``tasks.extract`` exactly: per-page
kwargs are merged with the top-level kwargs, ``flavor`` is lower-cased, and
``columns`` is dropped when ``flavor`` is ``lattice`` (it has no effect there).

.. note::
   Excalibur is slow-cadence (v1.0.1 in January 2025, nothing since). A Jupyter
   notebook with ``camelot.plot(table, kind='contour')`` is a faster-iterating
   alternative for picking ``table_areas`` / ``columns``. The functions here
   accept any dict in the same shape, so they work the same on a notebook-
   crafted rule -- you do not need Excalibur installed.

Example::

    >>> from invoice2data.extract.excalibur import excalibur_to_template
    >>> excalibur_to_template({
    ...     "flavor": "Stream",
    ...     "pages": {"1": {"table_areas": ["50,700,550,50"],
    ...                     "columns": ["100,200,300,400"]}},
    ... })
    [{'table_areas': ['50,700,550,50'], 'columns': ['100,200,300,400'], \
'pages': '1', 'flavor': 'stream'}]
"""

import json
from collections.abc import Mapping
from typing import Any


__all__ = ["excalibur_to_camelot_yaml", "excalibur_to_template"]

_DEFAULT_FLAVOR = "lattice"


def excalibur_to_template(
    rule_options: Mapping[str, Any] | str,
) -> list[dict[str, Any]]:
    """Convert an Excalibur ``rule_options`` export to invoice2data camelot blocks.

    Args:
        rule_options (Mapping[str, Any] | str): The Excalibur rule JSON (a
            mapping or a JSON-encoded string). Top-level keys: ``flavor``,
            ``pages`` (dict keyed by page-number string), plus any
            ``camelot.read_pdf`` kwargs shared across pages.

    Returns:
        list[dict[str, Any]]: One mapping per page, each ready to drop into a
            template's top-level ``camelot:`` block. Pages are NOT merged even
            when their kwargs match — keeps the round-trip honest and the
            template diff-able against the Excalibur rule.

    Raises:
        ValueError: When ``rule_options`` is a string that doesn't parse as JSON.
        TypeError: When ``rule_options`` (or its JSON-decoded form) is not a mapping.
    """
    if isinstance(rule_options, str):
        try:
            parsed = json.loads(rule_options)
        except json.JSONDecodeError as exc:
            raise ValueError(f"rule_options is not valid JSON: {exc}") from exc
    else:
        parsed = rule_options
    if not isinstance(parsed, Mapping):
        raise TypeError(
            "rule_options must be a mapping or a JSON object, got "
            f"{type(parsed).__name__}"
        )
    options = dict(parsed)
    flavor = str(options.pop("flavor", _DEFAULT_FLAVOR)).lower()
    pages = options.pop("pages", {}) or {}
    shared_kwargs = options  # everything else is shared across pages

    blocks: list[dict[str, Any]] = []
    for page_num, page_kwargs in pages.items():
        block: dict[str, Any] = dict(page_kwargs or {})
        block.update(shared_kwargs)
        block["pages"] = str(page_num)
        block["flavor"] = flavor
        # camelot's lattice parser ignores `columns`; Excalibur drops it
        # explicitly, so do the same to keep the template tidy.
        if flavor == "lattice":
            block.pop("columns", None)
        blocks.append(block)

    return blocks


def excalibur_to_camelot_yaml(
    rule_options: Mapping[str, Any] | str,
    *,
    field: str = "lines",
) -> str:
    """Render the converted blocks as a YAML snippet ready to paste in a template.

    Args:
        rule_options (Mapping[str, Any] | str): The Excalibur rule JSON.
        field (str): The invoice2data output key each table populates
            (forwarded to the ``camelot`` plugin's ``field`` option).

    Returns:
        str: A YAML document with a top-level ``camelot:`` list, e.g.::

            camelot:
            - table_areas: ['50,700,550,50']
              pages: '1'
              flavor: stream
              field: lines
    """
    import yaml  # type: ignore[import-untyped]

    blocks = excalibur_to_template(rule_options)
    for block in blocks:
        block.setdefault("field", field)
    rendered: str = yaml.safe_dump({"camelot": blocks}, sort_keys=False)
    return rendered
