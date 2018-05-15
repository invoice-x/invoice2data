import json
import datetime


def myconverter(o):
    """function to serialise datetime"""
    if isinstance(o, datetime.datetime):
        return o.__str__()


def write_to_file(data, path):
    """Export extracted fields to json

    Appends .json to path if missing and generates json file in specified directory, if not then in root

    Parameters
    ----------
    data : dict
        Dictionary of extracted fields
    path : str
        directory to save generated json file

    Notes
    ----
    Do give file name to the function parameter path.

    Examples
    --------
        >>> from invoice2data.output import to_json
        >>> to_json.write_to_file(data, "/exported_json/invoice.json")
        >>> to_json.write_to_file(data, "invoice.json")

    """
    if path.endswith('.json'):
        filename = path
    else:
        filename = path + '.json'

    with open(filename, "w") as json_file:
        for line in data:
            line['date'] = line['date'].strftime('%d/%m/%Y')
        json.dump(data, json_file, indent=4,  sort_keys=True, default = myconverter)
