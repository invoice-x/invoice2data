"""XML output module for invoice2data."""

import datetime
import importlib.util
from typing import Any
from typing import Dict
from typing import List
from xml.etree import ElementTree


def defusedxml_available() -> bool:
    """Checks if the defusedxml module is available.

    Returns:
        bool: True if defusedxml is available, False otherwise.
    """
    return importlib.util.find_spec("defusedxml") is not None


def prettify(elem: ElementTree.Element) -> Any:
    """Return a pretty-printed XML string for the Element.

    Args:
        elem (ElementTree.Element): The Element to be pretty-printed.

    Returns:
        Any: A pretty-printed XML string.
    """
    if defusedxml_available():
        from defusedxml import minidom  # type: ignore[import-not-found]
    else:
        from xml.dom import minidom

    rough_string = ElementTree.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)  # noqa S318
    return reparsed.toprettyxml(indent="  ")


def dict_to_tags(
    parent: ElementTree.Element, data: Dict[str, Any], date_format: str
) -> None:
    """Convert a dictionary to XML tags.

    This function iterates through the dictionary and creates XML tags
    for each key-value pair. It handles different data types and formats
    dates according to the specified format.

    Args:
        parent (ElementTree.Element): The parent element.
        data (Dict[str, Any]): The dictionary to be converted.
        date_format (str): The date format to use.
    """
    for k, v in data.items():
        tag = ElementTree.SubElement(parent, k)
        if isinstance(v, str):
            tag.text = v
        elif isinstance(v, (int, float)):
            tag.text = str(v)
        elif isinstance(v, datetime.date):
            tag.text = v.strftime(date_format)
        elif isinstance(v, list):
            for e in v:
                item = ElementTree.SubElement(tag, "item")
                dict_to_tags(item, e, date_format)


def write_to_file(
    data: List[Dict[str, Any]], path: str, date_format: str = "%Y-%m-%d"
) -> None:
    """Export extracted fields to xml.

    Appends .xml to path if missing and generates xml file in specified directory,
    if not then in root.

    Args:
        data (List[Dict[str, Any]]): List of dictionaries containing extracted fields.
        path (str): Path to save the generated XML file.
        date_format (str, optional): Date format used in generated file.
            Defaults to "%Y-%m-%d".

    Notes:
        Provide a filename to the `path` parameter.

    Examples:
        >>> from invoice2data.output import to_xml
        >>> data = [{'amount': 123.45, 'date': datetime.datetime(2024, 1, 1)}]
        >>> to_xml.write_to_file(data, "invoice.xml")
    """
    if not path.endswith(".xml"):
        filename = path + ".xml"
    else:
        filename = path

    tag_data = ElementTree.Element("data")
    with open(filename, "w") as xml_file:
        for i, line in enumerate(data):
            tag_item = ElementTree.SubElement(tag_data, "item")
            tag_item.set("id", str(i + 1))
            dict_to_tags(tag_item, line, date_format)

        xml_file.write(prettify(tag_data))
