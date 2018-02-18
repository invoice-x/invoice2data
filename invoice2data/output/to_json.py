import json

def write_to_file(data, path):
    with open(path, "w") as json_file:
        for line in data:
            json.dump({'date':line['date'].strftime('%d/%m/%Y'),
                      'desc':line['desc'],
                      'amount':line['amount']},json_file, indent = 4)
            json_file.write('\n')
            
