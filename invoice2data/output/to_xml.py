import xml.etree.ElementTree as ET
from xml.dom import minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def write_to_file(data, path):
    tag_data = ET.Element('data')
    xml_file = open(path, "w")
    i = 0
    for line in data:
        i += 1
        tag_item = ET.SubElement(tag_data, 'item')
        tag_date = ET.SubElement(tag_item, 'date')
        tag_desc = ET.SubElement(tag_item, 'desc')
        tag_amount = ET.SubElement(tag_item, 'amount')
        tag_item.set('id', str(i))
        tag_date.text = line['date'].strftime('%d/%m/%Y')
        tag_desc.text = line['desc']
        tag_amount.text = str(line['amount'])

    xml_file.write(prettify(tag_data))

