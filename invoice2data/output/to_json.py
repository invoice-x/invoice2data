import json


def write_to_file(data, path, dump_fields):
    if path.endswith('.json'):
        filename = path
    else:
        filename = path + '.json'
    print(dump_fields)
    if dump_fields:
        with open(filename, "w") as json_file:
            for line in data:
                line['date'] = line['date'].strftime('%d/%m/%Y')
            json.dump(data, json_file, indent=4,  sort_keys=True)
    else:
        with open(filename, "w") as json_file:
            for line in data:
                json.dump({'date':line['date'].strftime('%d/%m/%Y'),
                          'desc':line['desc'],
                          'currency':line['currency'],
                          'amount':line['amount']}, json_file, indent=4,  sort_keys=True)
                json_file.write('\n')

