"""Camelot table-extraction plugin (optional) for invoice2data.

Opt-in: requires the optional ``camelot-py`` dependency
(``pip install invoice2data[camelot]``). Unlike the text parsers/plugins,
camelot re-reads the PDF itself to detect ruled (``lattice``) or
whitespace-aligned (``stream``) tables, so it needs the source file path.

Enable it with a top-level ``camelot:`` block in a template — either a single
mapping or a list of them. Recognised ``camelot.read_pdf`` keys (``pages``,
``flavor``, ``table_areas``, ``columns``, ...) are forwarded as-is; the
plugin-specific keys are:

    field   output key to populate (default: ``lines``)
    header  use the table's first row as the column names (default: ``true``)
    tables  which detected table to use: an index, or ``all`` (default: ``all``)

Example::

    camelot:
      flavor: lattice
      pages: "1"
      field: lines
"""

from logging import getLogger
from typing import Any


logger = getLogger(__name__)

# ``camelot.read_pdf`` keyword arguments we forward verbatim. Anything else in
# the template block is treated as plugin configuration.
_READ_PDF_KEYS = frozenset(
    {
        "pages",
        "password",
        "flavor",
        "suppress_stdout",
        "parallel",
        "layout_kwargs",
        "table_areas",
        "table_regions",
        "columns",
        "split_text",
        "flag_size",
        "strip_text",
        "row_tol",
        "column_tol",
        "edge_tol",
        "line_scale",
        "shift_text",
        "process_background",
        "line_tol",
        "joint_tol",
        "threshold_blocksize",
        "threshold_constant",
        "iterations",
        "resolution",
        "backend",
    }
)


def is_available() -> bool:
    """Return whether the optional ``camelot-py`` package is importable.

    Returns:
        bool: True if ``camelot`` is installed.
    """
    import importlib.util

    return importlib.util.find_spec("camelot") is not None


def extract(
    self: Any,
    content: str,
    output: dict[str, Any],
    invoice_file: str | None = None,
) -> None:
    """Detect tables with camelot and add their rows to the output.

    Args:
        self (Any): The matched template (an InvoiceTemplate); provides the
            ``camelot:`` block.
        content (str): Unused — camelot reads the PDF directly.
        output (dict[str, Any]): Output dictionary to populate.
        invoice_file (str | None): Path to the source PDF (required).
    """
    if not is_available():
        logger.warning(
            "Template %s uses the 'camelot' plugin but camelot-py is not "
            "installed; install it with `pip install invoice2data[camelot]`.",
            self.get("template_name"),
        )
        return
    if not invoice_file:
        logger.warning("camelot plugin needs the invoice file path; skipping")
        return

    import camelot

    block = self["camelot"]
    rules = block if isinstance(block, list) else [block]
    for rule in rules:
        rule = dict(rule)
        field = rule.pop("field", "lines")
        header = rule.pop("header", True)
        which = rule.pop("tables", "all")
        read_kwargs = {key: rule[key] for key in rule if key in _READ_PDF_KEYS}
        unknown = set(rule) - _READ_PDF_KEYS
        if unknown:
            logger.warning("camelot: ignoring unknown option(s) %s", sorted(unknown))

        try:
            tables = camelot.read_pdf(invoice_file, **read_kwargs)
        except Exception:
            logger.exception("camelot.read_pdf failed for %s", invoice_file)
            continue

        selected = tables if which == "all" else [tables[int(which)]]
        records: list[dict[str, Any]] = []
        for table in selected:
            records.extend(_rows_to_records(table.data, header))
        logger.debug("camelot extracted %d row(s) into '%s'", len(records), field)
        if records:
            output[field] = records


def _rows_to_records(rows: list[list[str]], header: bool) -> list[dict[str, Any]]:
    """Convert camelot rows (a list of cell lists) into a list of dicts.

    Args:
        rows (list[list[str]]): Table cells row by row, as returned by camelot's
            ``Table.data``.
        header (bool): Use the first row as the column names; otherwise generate
            ``col_0``, ``col_1``, ... keys.

    Returns:
        list[dict[str, Any]]: One dict per body row, keyed by column name.
    """
    if not rows:
        return []
    if header:
        keys = [str(cell).strip() for cell in rows[0]]
        body = rows[1:]
    else:
        keys = [f"col_{index}" for index in range(len(rows[0]))]
        body = rows
    return [
        {key: str(value).strip() for key, value in zip(keys, row, strict=False)}
        for row in body
    ]
