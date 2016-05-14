import yaml
import os
import re
import dateparser
from unidecode import unidecode
import logging as logger

OPTIONS_DEFAULT = {
    'remove_whitespace': False,
    'remove_accents': False,
    'lowercase': False,
    'currency': 'EUR',
    'date_formats': [],
    'languages': [],
    'decimal_separator': '.',
    'replace': [],  # example: see templates/fr/fr.free.mobile.yml
}

def read_templates(folder):
    """
    Load yaml templates from template folder. Return list of dicts.
    """
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

                output.append(InvoiceTemplate(tpl))
    return output


class InvoiceTemplate(dict):
    """
    Represents single template files that live as .yml files on the disk.
    """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

        # Merge template-specific options with defaults
        self.options = OPTIONS_DEFAULT.copy()

        for lang in self.options['languages']:
            assert len(lang) == 2, 'lang code must have 2 letters'

        if 'options' in self:
            self.options.update(self['options'])

        # Set issuer, if it doesn't exist.
        if 'issuer' not in self.keys():
            self['issuer'] = self['keywords'][0]

    def prepare_input(self, extracted_str):
        """
        Input raw string and do transformations, as set in template file.
        """

        # Remove withspace
        if self.options['remove_whitespace']:
            optimized_str = re.sub(' +', '', extracted_str)
        else:
            optimized_str = extracted_str
        
        # Remove accents
        if self.options['remove_accents']:
            optimized_str = unidecode(optimized_str)

        # specific replace
        for replace in self.options['replace']:
            assert len(replace) == 2, 'A replace should be a list of 2 items'
            optimized_str = optimized_str.replace(replace[0], replace[1])

        return optimized_str

    def matches_input(self, optimized_str):
        """See if string matches keywords set in template file"""

        if all([keyword in optimized_str for keyword in self['keywords']]):
            logger.debug('Matched template %s', self['template_name'])
            return True

    def extract(self, optimized_str):
        """
        Given a template file and a string, extract matching data fields.
        """

        logger.debug('START optimized_str ========================')
        logger.debug(optimized_str)
        logger.debug('END optimized_str ==========================')
        logger.debug(
            'Date parsing: languages=%s date_formats=%s',
            self.options['languages'], self.options['date_formats'])
        logger.debug('Float parsing: decimal separator=%s', self.options['decimal_separator'])
        logger.debug("keywords=%s", self['keywords'])
        logger.debug(self.options)

        # Try to find data for each field.
        output = {}
        for k, v in self['fields'].items():
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
                            raw_date, date_formats=self.options['date_formats'],
                            languages=self.options['languages'])
                        logger.debug("result of date parsing=%s", output[k])
                        if not output[k]:
                            logger.error(
                                "Date parsing failed on date '%s'", raw_date)
                            return None
                    elif k.startswith('amount'):
                        assert res_find[0].count(self.options['decimal_separator']) < 2,\
                            'Decimal separator cannot be present several times'
                        # replace decimal separator by a |
                        amount_pipe = res_find[0].replace(self.options['decimal_separator'], '|')
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

        output['currency'] = self.options['currency']

        if len(output.keys()) >= 4:
            output['desc'] = 'Invoice %s from %s' % (
                output['invoice_number'], self['issuer'])
            logger.debug(output)
            return output
        else:
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
