import csv
import sys


def write_to_file(data, path):
    """Export extracted fields to csv

    Appends .csv to path if missing and generates csv file in specified directory, if not then in root

    Parameters
    ----------
    data : dict
        Dictionary of extracted fields
    path : str
        directory to save generated csv file

    Notes
    ----
    Do give file name to the function parameter path.

    Examples
    --------
        >>> from invoice2data.output import to_csv
        >>> to_csv.write_to_file(data, "/exported_csv/invoice.csv")
        >>> to_csv.write_to_file(data, "invoice.csv")

    """
    if path.endswith('.csv'):
        filename = path
    else:
        filename = path + '.csv'

    if sys.version_info[0] < 3:
        openfile = open(filename, "wb")
    else:
        openfile = open(filename, "w", newline='')

    keys = data[0].keys()
    with openfile as csv_file:
        dict_writer = csv.DictWriter(csv_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
