import datetime
import json


def format_item(item, date_format):
    """Format an item for JSON serialization.

    Args:
        item: The item to format.
        date_format: The date format to use.

    Returns:
        The formatted item.
    """
    if isinstance(item, datetime.date):
        return item.strftime(date_format)
    if isinstance(item, (dict, list)):
        # Use a consistent way to iterate and format nested items
        iter_obj = item.items() if isinstance(item, dict) else enumerate(item)
        for k, v in iter_obj:
            item[k] = format_item(v, date_format)
    return item


def write_to_file(data, path, date_format="%Y-%m-%d"):
    """Export extracted fields to JSON.

    Appends .json to path if missing and generates JSON file in
    the specified directory, otherwise in the current directory.

    Args:
        data (dict): Dictionary of extracted fields.
        path (str): Directory to save the generated JSON file.
        date_format (str, optional): Date format used in the
                                     generated file.
                                     Defaults to "%Y-%m-%d".

    Notes:
        Provide a filename to the `path` parameter.

    Examples:
        >>> from invoice2data.output import to_json
        >>> to_json.write_to_file(data, "/exported_json/invoice.json")
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
