import csv
import sys


def write_to_file(data: list, path: str, date_format="%Y-%m-%d") -> None:
    """Export extracted fields to csv

    Appends .csv to path if missing and generates csv file in specified directory, if not then in root

    Parameters
    ----------
    data : list
        A list of dictionaries of extracted fields.
        If only a single file was processed, it must be passed as a single-element list.
    path : str
        csv file to save output csv to
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

        for line in data:
            first_row = []
            for k, v in line.items():
                first_row.append(k)

        writer.writerow(first_row)
        for line in data:
            csv_items = []
            for k, v in line.items():
                # first_row.append(k)
                if k.startswith("date") or k.endswith("date"):
                    v = v.strftime(date_format)
                csv_items.append(v)
            writer.writerow(csv_items)
