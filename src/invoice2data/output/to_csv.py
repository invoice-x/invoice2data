"""CSV output module for invoice2data."""

import csv
import datetime
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .to_json import format_item


def _cell(value: Any, date_format: str) -> Any:
    """Render a single CSV cell value.

    Dates are formatted with ``date_format``; lists/dicts (e.g. ``lines`` and
    ``tax_lines``) are JSON-encoded so the CSV stays valid and machine-readable
    instead of holding a Python ``repr``.

    Args:
        value (Any): The field value.
        date_format (str): strftime format used for dates.

    Returns:
        Any: A CSV-safe scalar value.
    """
    if isinstance(value, datetime.date):
        return value.strftime(date_format)
    if isinstance(value, list | dict):
        return json.dumps(format_item(deepcopy(value), date_format), ensure_ascii=False)
    return value


def _write_flat(writer: Any, data: list[dict[str, Any]], date_format: str) -> None:
    """Write one row per invoice; list/dict fields are JSON-encoded.

    Args:
        writer (Any): A ``csv.writer`` instance.
        data (list[dict[str, Any]]): The extracted invoices.
        date_format (str): strftime format used for dates.
    """
    last_header = None
    for invoice in data:
        header = list(invoice.keys())
        if header != last_header:
            writer.writerow(header)
            last_header = header
        writer.writerow([_cell(value, date_format) for value in invoice.values()])


def _write_exploded(writer: Any, data: list[dict[str, Any]], date_format: str) -> None:
    """Write one row per ``lines`` item, repeating invoice-level fields.

    Line-item fields are emitted as ``line_<name>`` columns. Other list/dict
    fields (e.g. ``tax_lines``) remain JSON-encoded.

    Args:
        writer (Any): A ``csv.writer`` instance.
        data (list[dict[str, Any]]): The extracted invoices.
        date_format (str): strftime format used for dates.
    """
    last_header = None
    for invoice in data:
        scalars = {key: value for key, value in invoice.items() if key != "lines"}
        line_items = invoice.get("lines") or [{}]
        line_keys: list[str] = []
        for item in line_items:
            for key in item:
                if key not in line_keys:
                    line_keys.append(key)
        header = list(scalars.keys()) + [f"line_{key}" for key in line_keys]
        for item in line_items:
            if header != last_header:
                writer.writerow(header)
                last_header = header
            row = [_cell(value, date_format) for value in scalars.values()]
            row += [_cell(item.get(key, ""), date_format) for key in line_keys]
            writer.writerow(row)


def write_to_file(
    data: list[dict[str, Any]],
    path: str,
    date_format: str = "%Y-%m-%d",
    lines_mode: str = "json",
) -> None:
    """Export extracted fields to CSV.

    Appends .csv to path if missing and generates a CSV file in the specified
    directory, otherwise in the current directory.

    Args:
        data (list[dict[str, Any]]): A list of dictionaries of extracted fields.
            If only a single file was processed, it must be passed as a
            single-element list.
        path (str): CSV file to save output to.
        date_format (str): Date format used in the generated file.
            Defaults to "%Y-%m-%d".
        lines_mode (str): How to render line-item arrays. "json" (default)
            JSON-encodes ``lines``/``tax_lines`` cells; "explode" writes one row
            per ``lines`` item, repeating invoice-level fields.

    Notes:
        Provide a filename to the `path` parameter.

    Examples:
        >>> from invoice2data.output import to_csv
        >>> data = [{'amount': 123.45, 'date': datetime.datetime(2024, 1, 1)}]
        >>> to_csv.write_to_file(data, "invoice.csv")
    """
    filename = path if path.endswith(".csv") else path + ".csv"

    with Path(filename).open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        if lines_mode == "explode":
            _write_exploded(writer, data, date_format)
        else:
            _write_flat(writer, data, date_format)
