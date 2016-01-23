import yaml
import os

def read_templates(folder):
    "Load yaml templates from template folder. Return dict."

    output = []
    for path, subdirs, files in os.walk(folder):
        for name in files:
            print(os.path.join(path, name))
            if name.endswith('.yml'):
                tpl = yaml.load(open(os.path.join(path, name)).read())

                # Test if all required fields are in template:
                assert 'keywords' in tpl.keys(), 'Missing keywords field.'
                required_fields = ['date', 'amount', 'invoice_number']
                assert len(required_fields & tpl['fields'].keys()) == len(required_fields), \
                    'Missing required key in template {} {}. Found {}'.format(name, path, tpl['fields'].keys())
                
                # Keywords as list, if only one.
                if type(tpl['keywords']) is not list:
                    tpl['keywords'] = [tpl['keywords']]

                output.append(tpl)
    return output

def dict_to_yml(dict_in, identifier):
    "Convert old templates to new yml format."
    dict_in['fields'] = {t[0]: t[1] for t in dict_in['data']}
    dict_in.pop('data')
    yaml_str = yaml.dump(dict_in, default_flow_style=False, allow_unicode=True)
    with open('templates/{}.yml'.format(identifier), 'w') as f:
        f.write(yaml_str)
    
if __name__ == '__main__':
    for t in templates:
        dict_to_yml(t, t['keywords'][0].lower().replace(' ', ''))
