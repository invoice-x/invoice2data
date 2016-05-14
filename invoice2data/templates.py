import yaml
import os
import re
import dateparser
import logging as logger

def read_templates(folder):
    "Load yaml templates from template folder. Return dict."
    output = []
    for path, subdirs, files in os.walk(folder):
        for name in files:
            if name.endswith('.yml'):
                tpl = yaml.load(open(os.path.join(path, name)).read())
                tpl['template_name'] = name

                # Test if all required fields are in template:
                assert 'keywords' in tpl.keys(), 'Missing keywords field.'
                required_fields = ['date', 'amount', 'invoice_number']
                assert len(set(required_fields).intersection(tpl['fields'].keys())) == len(required_fields), \
                    'Missing required key in template {} {}. Found {}'.format(name, path, tpl['fields'].keys())
                
                # Keywords as list, if only one.
                if type(tpl['keywords']) is not list:
                    tpl['keywords'] = [tpl['keywords']]

                output.append(tpl)
    return output



def extract_with_template(t, optimized_str, run_options):
    """
    Given a template file and a string, extract matching data fields.
    """

    logger.debug('START optimized_str ========================')
    logger.debug(optimized_str)
    logger.debug('END optimized_str ==========================')
    date_formats = run_options['date_formats']
    languages = run_options['languages']
    decimal_sep = run_options['decimal_separator']
    for lang in languages:
        assert len(lang) == 2, 'lang code must have 2 letters'
    logger.debug(
        'Date parsing: languages=%s date_formats=%s',
        languages, date_formats)
    logger.debug('Float parsing: decimal separator=%s', decimal_sep)
    logger.debug("keywords=%s", t['keywords'])
    logger.debug(run_options)

    # Try to find data for each field.
    output = {}
    for k, v in t['fields'].items():
        if k.startswith('static_'):
            logger.debug("field=%s | static value=%s", k, v)
            output[k.replace('static_', '')] = v
        else:
            logger.debug("field=%s | regexp=%s", k, v)

            # Fields can have multiple expressions
            if type(v) is list:
                for v_option in v:
                    res_find = re.findall(v_option, optimized_str)
                    if res_find:
                        break
            else:
                res_find = re.findall(v, optimized_str)
            if res_find:
                logger.debug("res_find=%s", res_find)
                if k.startswith('date'):
                    raw_date = res_find[0]
                    output[k] = dateparser.parse(
                        raw_date, date_formats=date_formats,
                        languages=languages)
                    logger.debug("result of date parsing=%s", output[k])
                    if not output[k]:
                        logger.error(
                            "Date parsing failed on date '%s'", raw_date)
                        return None
                elif k.startswith('amount'):
                    assert res_find[0].count(decimal_sep) < 2,\
                        'Decimal separator cannot be present several times'
                    # replace decimal separator by a |
                    amount_pipe = res_find[0].replace(decimal_sep, '|')
                    # remove all possible thousands separators
                    amount_pipe_no_thousand_sep = re.sub(
                        '[.,\s]', '', amount_pipe)
                    # put dot as decimal sep
                    amount_regular = amount_pipe_no_thousand_sep.replace('|', '.')
                    # it is now safe to convert to float
                    output[k] = float(amount_regular)
                else:
                    output[k] = res_find[0]
            else:
                logger.warning("regexp for field %s didn't match", k)

    # TODO remove after all templates have issuer set.
    if 'issuer' not in t.keys():
        identifier = t['keywords'][0]
    else:
        identifier = t['issuer']

    output['currency'] = run_options['currency']

    if len(output.keys()) >= 4:
        output['desc'] = 'Invoice %s from %s' % (
            output['invoice_number'], identifier)
        logger.debug(output)
        return output
    else:
        logger.error('Missing some fields for file %s', invoicefile)
        logger.error(output)
        return None


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
