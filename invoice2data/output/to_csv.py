import csv
import sys


def write_to_file(data, path, dump_fields):
    if path.endswith('.csv'):
        filename = path
    else:
        filename = path + '.csv'

    if sys.version_info[0] < 3:
        openfile = open(filename, "wb")
    else:
        openfile = open(filename, "w", newline='')

    with openfile as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        if dump_fields:
            for line in data:
                first_row = []
                for k, v in line.items():
                    first_row.append(k)

            writer.writerow(first_row)
            for line in data:
                csv_items = []
                for k, v in line.items():
                    # first_row.append(k)
                    if k == 'date':
                        v = v.strftime('%d/%m/%Y')
                    csv_items.append(v)
                writer.writerow(csv_items)
        else:
            writer.writerow(['date', 'desc', 'currency', 'amount'])
            for line in data:
                writer.writerow([
                    line['date'].strftime('%d/%m/%Y'),
                    line['desc'],
                    line['currency'],
                    line['amount']])
