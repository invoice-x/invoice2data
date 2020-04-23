import xml.etree.ElementTree as ET
import datetime
from xml.dom import minidom


def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def dict_to_tags(parent, data, date_format):
    for k, v in data.items():
        tag = ET.SubElement(parent, k)
        if isinstance(v, str):
            tag.text = v
        elif isinstance(v, int) or isinstance(v, float):
            tag.text = str(v)
        elif isinstance(v, datetime.date):
            tag.text = v.strftime(date_format)
        elif isinstance(v, list):
            for e in v:
                item = ET.SubElement(tag, "item")
                dict_to_tags(item, e, date_format)


def write_to_file(data, path, date_format="%Y-%m-%d"):
    """Export extracted fields to xml

    Appends .xml to path if missing and generates xml file in specified directory, if not then in root

    Parameters
    ----------
    data : dict
        Dictionary of extracted fields
    path : str
        directory to save generated xml file
    date_format : str
        Date format used in generated file

    Notes
    ----
    Do give file name to the function parameter path.

    Examples
    --------
        >>> from invoice2data.output import to_xml
        >>> to_xml.write_to_file(data, "/exported_xml/invoice.xml")
        >>> to_xml.write_to_file(data, "invoice.xml")

    """

    if path.endswith(".xml"):
        filename = path
    else:
        filename = path + ".xml"

    tag_data = ET.Element("data")
    xml_file = open(filename, "w")
    i = 0
    for line in data:
        i += 1
        tag_item = ET.SubElement(tag_data, "item")
        tag_item.set("id", str(i))
        dict_to_tags(tag_item, line, date_format)

    xml_file.write(prettify(tag_data))
    xml_file.close()
