import json
import datetime
import codecs


def myconverter(o):
    """function to serialise datetime"""
    if isinstance(o, datetime.datetime):
        return o.__str__()


def write_to_file(data, path, date_format="%Y-%m-%d"):
    """Export extracted fields to json

    Appends .json to path if missing and generates json file in specified directory, if not then in root

    Parameters
    ----------
    data : dict
        Dictionary of extracted fields
    path : str
        directory to save generated json file
    date_format : str
        Date format used in generated file

    Notes
    ----
    Do give file name to the function parameter path.

    Examples
    --------
        >>> from invoice2data.output import to_json
        >>> to_json.write_to_file(data, "/exported_json/invoice.json")
        >>> to_json.write_to_file(data, "invoice.json")

    """
    if path.endswith(".json"):
        filename = path
    else:
        filename = path + ".json"

    with codecs.open(filename, "w", encoding="utf-8") as json_file:
        for line in data:
            for k, v in line.items():
                if k.startswith("date") or k.endswith("date"):
                    line[k] = v.strftime(date_format)
        json.dump(
            data,
            json_file,
            indent=4,
            sort_keys=False,
            default=myconverter,
            ensure_ascii=False,
        )
