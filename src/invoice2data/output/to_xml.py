"""XML output module for invoice2data."""

import datetime
import xml.etree.ElementTree as ET

from defusedxml import minidom


def prettify(elem):
    """Return a pretty-printed XML string for the Element.

    Args:
        elem: The Element to be pretty-printed.

    Returns:
        str: A pretty-printed XML string.
    """
    rough_string = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def dict_to_tags(parent, data, date_format):
    """Convert a dictionary to XML tags.

    Args:
        parent: The parent element.
        data: The dictionary to be converted.
        date_format: The date format to use.
    """
    for k, v in data.items():
        tag = ET.SubElement(parent, k)
        if isinstance(v, str):
            tag.text = v
        elif isinstance(v, (int, float)):
            tag.text = str(v)
        elif isinstance(v, datetime.date):
            tag.text = v.strftime(date_format)
        elif isinstance(v, list):
            for e in v:
                item = ET.SubElement(tag, "item")
                dict_to_tags(item, e, date_format)


def write_to_file(data, path, date_format="%Y-%m-%d"):
    """Export extracted fields to xml.

    Appends .xml to path if missing and generates xml file in specified directory,
    if not then in root.

    Args:
        data (dict): Dictionary of extracted fields.
        path (str): Directory to save generated xml file.
        date_format (str, optional): Date format used in generated file.
            Defaults to "%Y-%m-%d".

    Notes:
        Do give file name to the function parameter path.

    Examples:
        >>> from invoice2data.output import to_xml
        >>> to_xml.write_to_file(data, "/exported_xml/invoice.xml")
        >>> to_xml.write_to_file(data, "invoice.xml")
    """
    if not path.endswith(".xml"):
        filename = path + ".xml"
    else:
        filename = path

    tag_data = ET.Element("data")
    with open(filename, "w") as xml_file:
        for i, line in enumerate(data):
            tag_item = ET.SubElement(tag_data, "item")
            tag_item.set("id", str(i + 1))
            dict_to_tags(tag_item, line, date_format)

        xml_file.write(prettify(tag_data))
