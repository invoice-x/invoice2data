"""
This module abstracts templates for invoice providers. 

Templates are initially read from .yml files and then kept as class.
"""

import yaml
import os
import re
import dateparser
from unidecode import unidecode
import logging as logger
from collections import OrderedDict

from invoice2data.utils import ordered_load

OPTIONS_DEFAULT = {
    'remove_whitespace': False,
    'remove_accents': False,
    'lowercase': False,
    'currency': 'EUR',
    'date_formats': [],
    'languages': [],
    'decimal_separator': '.',
    'replace': [],  # example: see templates/fr/fr.free.mobile.yml
    'field_separator': r'\s+',
    'line_separator': r'\n',
}

def read_templates(folder):
    """
    Load yaml templates from template folder. Return list of dicts.
    """
    output = []
    for path, subdirs, files in os.walk(folder):
        for name in files:
            if name.endswith('.yml'):
                tpl = ordered_load(open(os.path.join(path, name)).read())
                tpl['template_name'] = name

                # Test if all required fields are in template:
                assert 'keywords' in tpl.keys(), 'Missing keywords field.'
                required_fields = ['date', 'amount', 'invoice_number']
                assert len(set(required_fields).intersection(tpl['fields'].keys())) == len(required_fields), \
                    'Missing required key in template {} {}. Found {}'.format(name, path, tpl['fields'].keys())
                
                # Keywords as list, if only one.
                if type(tpl['keywords']) is not list:
                    tpl['keywords'] = [tpl['keywords']]

                if 'lines' in tpl:
                    assert 'start' in tpl['lines'], 'Lines start regex missing'
                    assert 'end' in tpl['lines'], 'Lines end regex missing'
                    assert 'line' in tpl['lines'], 'Line regex missing'

                output.append(InvoiceTemplate(tpl))
    return output


class InvoiceTemplate(OrderedDict):
    """
    Represents single template files that live as .yml files on the disk.
    """

    def __init__(self, *args, **kwargs):
        super(InvoiceTemplate, self).__init__(*args, **kwargs)

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

        # convert to lower case
        if self.options['lowercase']:
            optimized_str = optimized_str.lower()

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

    def parse_number(self, value):
        assert value.count(self.options['decimal_separator']) < 2,\
            'Decimal separator cannot be present several times'
        # replace decimal separator by a |
        amount_pipe = value.replace(self.options['decimal_separator'], '|')
        # remove all possible thousands separators
        amount_pipe_no_thousand_sep = re.sub(
            '[.,\s]', '', amount_pipe)
        # put dot as decimal sep
        return float(amount_pipe_no_thousand_sep.replace('|', '.'))

    def coerce_type(self, value, target_type):
        if target_type == 'int':
            if not value.strip():
                return 0
            return int(self.parse_number(value))
        elif target_type == 'float':
            if not value.strip():
                return 0.0
            return float(self.parse_number(value))
        assert False, 'Unknown type'

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
                        output[k] = self.parse_number(res_find[0])
                    else:
                        output[k] = res_find[0]
                else:
                    logger.warning("regexp for field %s didn't match", k)

        if 'lines' in self:
            self.extract_lines(optimized_str, output)

        output['currency'] = self.options['currency']

        if len(output.keys()) >= 4:
            output['desc'] = 'Invoice %s from %s' % (
                output['invoice_number'], self['issuer'])
            logger.debug(output)
            return output
        else:
            logger.error(output)
            return None

    def extract_lines(self, content, output):
        """Try to extract lines from the invoice"""
        start = re.search(self['lines']['start'], content)
        end = re.search(self['lines']['end'], content)
        if not start or not end:
            logger.warning('no lines found - start %s, end %s', start, end)
            return
        content = content[start.end():end.start()]
        lines = []
        current_row = {}
        for line in re.split(self.options['line_separator'], content):
            if 'first_line' in self['lines']:
                match = re.search(self['lines']['first_line'], line)
                if match:
                    if current_row:
                        lines.append(current_row)
                    current_row = {
                        field: value.strip()
                        for field, value in match.groupdict().items()
                    }
                    continue
            if 'last_line' in self['lines']:
                match = re.search(self['lines']['last_line'], line)
                if match:
                    for field, value in match.groupdict().items():
                        current_row[field] = '%s%s%s' % (
                            current_row.get(field, ''),
                            current_row.get(field, '') and '\n' or '',
                            value.strip()
                        )
                    lines.append(current_row)
                    current_row = {}
                    continue
            match = re.search(self['lines']['line'], line)
            if match:
                for field, value in match.groupdict().items():
                    current_row[field] = '%s%s%s' % (
                        current_row.get(field, ''),
                        current_row.get(field, '') and '\n' or '',
                        value.strip()
                    )
                continue
            logger.warning(
                'ignoring *%s* because it doesn\'t match anything', line
            )
        if current_row:
            lines.append(current_row)

        types = self['lines'].get('types', [])
        for row in lines:
            for name in row.keys():
                if name in types:
                    row[name] = self.coerce_type(row[name], types[name])

        if lines:
            output['lines'] = lines
