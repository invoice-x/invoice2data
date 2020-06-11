import xml.etree.ElementTree as ET
from xml.dom import minidom


def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


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
    Only `date`, `desc`, `amount` and `currency` are exported

    Examples
    --------
        >>> from invoice2data.output import to_xml
        >>> to_xml.write_to_file(data, "/exported_xml/invoice.xml")
        >>> to_xml.write_to_file(data, "invoice.xml")

    """

    if path.endswith('.xml'):
        filename = path
    else:
        filename = path + '.xml'
    
    xml_file = open(filename, "w")
    tag_data = ET.Element('data')
    data = data[0]
    for line in data:
        if type(data[line]) == list:
            tag_list = ET.SubElement(tag_data, 'lines')
            i = 1
            for line_dict in data[line]:
                tag_line = ET.SubElement(tag_list, 'line')
                tag_line.set('id', str(i))
                i = i+1
                for line_item in line_dict:
                    tag_item = ET.SubElement(tag_line, line_item)
                    tag_item.text = str(line_dict[line_item])
        elif type(data[line]) == datetime:
            tag_item = ET.SubElement(tag_data, line)
            tag_item.text = data[line].strftime(date_format)
        else:
            tag_item = ET.SubElement(tag_data, line)
            tag_item.text = str(data[line])

    xml_file.write(prettify(tag_data))
    xml_file.close()
