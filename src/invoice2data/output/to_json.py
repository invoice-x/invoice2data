"""JSON output module for invoice2data."""

import datetime
import json
from typing import Any
from typing import Dict
from typing import List


def format_item(item: Any, date_format: str) -> Any:
    """Format an item for JSON serialization.

    Args:
        item (Any): The item to format.
        date_format (str): The date format to use.

    Returns:
        Any: The formatted item.
    """
    if isinstance(item, datetime.date):
        return item.strftime(date_format)
    if isinstance(item, (dict, list)):
        iter_obj = item.items() if isinstance(item, dict) else enumerate(item)
        for k, v in iter_obj:
            item[k] = format_item(v, date_format)
    return item


def write_to_file(
    data: List[Dict[str, Any]], path: str, date_format: str = "%Y-%m-%d"
) -> None:
    """Export extracted fields to JSON.

    Appends .json to path if missing and generates JSON file in
    the specified directory, otherwise in the current directory.

    Args:
        data (List[Dict[str, Any]]): Dictionary of extracted fields.
        path (str): Directory to save the generated JSON file.
        date_format (str): Date format used in the generated file.
                            Defaults to "%Y-%m-%d".

    Notes:
        Provide a filename to the `path` parameter.

    Examples:
        >>> from invoice2data.output import to_json
        >>> data = [{'amount': 123.45, 'date': datetime.datetime(2024, 1, 1)}]
        >>> to_json.write_to_file(data, "invoice.json")
    """
    for invoice in data:
        for k, v in invoice.items():
            invoice[k] = format_item(v, date_format)

    if not path.endswith(".json"):
        filename = path + ".json"
    else:
        filename = path

    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
