import csv

def write_to_file(data, path):
    if path.endswith('.csv'):
        filename = path
    else:
        filename = path + '.csv'
        
    with open(filename, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(['date', 'desc', 'currency', 'amount'])
        for line in data:
            writer.writerow([
                line['date'].strftime('%d/%m/%Y'),
                line['desc'],
                line['currency'],
                line['amount']])
