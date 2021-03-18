import csv
import sys


def write_to_file(data, path, date_format="%Y-%m-%d"):
    """Export extracted fields to csv

    Appends .csv to path if missing and generates csv file in specified directory, if not then in root

    Parameters
    ----------
    data : dict
        Dictionary of extracted fields
    path : str
        directory to save generated csv file
    date_format : str
        Date format used in generated file

    Notes
    ----
    Do give file name to the function parameter path.

    Examples
    --------
        >>> from invoice2data.output import to_csv
        >>> to_csv.write_to_file(data, "/exported_csv/invoice.csv")
        >>> to_csv.write_to_file(data, "invoice.csv")

    """
    if path.endswith(".csv"):
        filename = path
    else:
        filename = path + ".csv"

    if sys.version_info[0] < 3:
        openfile = open(filename, "wb")
    else:
        openfile = open(filename, "w", newline="")

    with openfile as csv_file:
        writer = csv.writer(csv_file, delimiter=",")

        # Write header to csv
        writer.writerow(data.keys())

        # Loop through data and see which had lists of results (e.g. from lines parser)
        csv_items = []
        for key in data.keys():
            value = data[key]
            if isinstance(value, list):
                # List of results, process each in turn
                result_list = []
                for item in value:
                    if isinstance(item, dict):
                        # The item in the list is a dictionary, so parse each key-value pair for datetime formatting
                        for sub_key in item.keys():
                            sub_value = item[sub_key]
                            if sub_key.startswith("date") or sub_key.endswith("date"):
                                # Key appears to indicate a date, so parse it as such
                                sub_value = sub_value.strftime(date_format)
                    result_list.append(item)
                csv_items.append(result_list)
            else:
                # Single value, so parse as date if necessary
                if key.startswith("date") or key.endswith("date"):
                    value = value.strftime(date_format)
                csv_items.append(value)
        writer.writerow(csv_items)
