"""CSV output module for invoice2data."""

import csv
import datetime  # noqa
from typing import Any
from typing import Dict
from typing import List


def write_to_file(
    data: List[Dict[str, Any]], path: str, date_format: str = "%Y-%m-%d"
) -> None:
    """Export extracted fields to CSV.

    Appends .csv to path if missing and generates a CSV file in the specified
    directory, otherwise in the current directory.

    Args:
        data (List[Dict[str, Any]]): A list of dictionaries of extracted fields. If only a
                            single file was processed, it must be passed as a
                            single-element list.
        path (str): CSV file to save output to.
        date_format (str): Date format used in the generated file.
                            Defaults to "%Y-%m-%d".

    Notes:
        Provide a filename to the `path` parameter.

    Examples:
        >>> from invoice2data.output import to_csv
        >>> data = [{'amount': 123.45, 'date': datetime.datetime(2024, 1, 1)}]
        >>> to_csv.write_to_file(data, "invoice.csv")
    """
    if not path.endswith(".csv"):
        filename = path + ".csv"
    else:
        filename = path

    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")

        last_header = None
        for line in data:
            header = list(line.keys())

            if header != last_header:
                writer.writerow(header)
                last_header = header

            csv_items = []
            for k, v in line.items():
                if k.startswith("date") or k.endswith("date"):
                    v = v.strftime(date_format)  # Assuming v is a date object
                csv_items.append(v)
            writer.writerow(csv_items)
