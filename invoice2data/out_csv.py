import csv

def invoices_to_csv(data, path):
    with open(path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(['date', 'desc', 'amount'])
        for line in data:
            writer.writerow([
                line['date'].strftime('%d/%m/%Y'),
                line['desc'],
                line['amount']])
