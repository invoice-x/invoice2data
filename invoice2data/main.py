#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import shutil
from os import listdir
from os.path import isfile, isdir, join
import locale
import pkg_resources
import invoice2data.pdftotext as pdftotext
import invoice2data.image_to_text as image_to_text
from invoice2data.templates import read_templates, extract_with_template
from invoice2data.output import invoices_to_csv
import logging
from unidecode import unidecode

logger = logging.getLogger(__name__)

FILENAME = "{date} {desc}.pdf"

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

def extract_data(invoicefile, OPTIONS_DEFAULT, templates=None, debug=False):
    if templates is None:
        templates = read_templates(
            pkg_resources.resource_filename('invoice2data', 'templates'))
    
    extracted_str = pdftotext.to_text(invoicefile).decode('utf-8')

    # Try OCR, when we get an almost empty str.
    charcount = len(extracted_str)
    logger.debug('number of char in pdf2text extract: %d', charcount)
    #if charcount < 40:
        #logger.info('Starting OCR')
        #extracted_str = image_to_text.to_text(invoicefile)
    logger.debug('START pdftotext result ===========================')
    logger.debug(extracted_str)
    logger.debug('END pdftotext result =============================')

    logger.debug('Testing {} template files'.format(len(templates)))

    for t in templates:
        # Merge template-specific options with defaults
        run_options = OPTIONS_DEFAULT.copy()
        if 'options' in t:
            run_options.update(t['options'])

        # Remove withspace
        if run_options['remove_whitespace']:
            optimized_str = re.sub(' +', '', extracted_str)
        else:
            optimized_str = extracted_str
        
        # Remove accents
        if run_options['remove_accents']:
            optimized_str = unidecode(optimized_str)

        # specific replace
        for replace in run_options['replace']:
            assert len(replace) == 2, 'A replace should be a list of 2 items'
            optimized_str = optimized_str.replace(replace[0], replace[1])

        if all([keyword in optimized_str for keyword in t['keywords']]):
            logger.debug('Matched template %s', t['template_name'])
            extract_with_template(t, optimized_str, run_options)

    logger.error('No template for %s', invoicefile)
    logger.debug(output)
    return False

def main():
    "Take folder or single file and analyze each."

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Print debug information.')

    parser.add_argument('--copy', '-c', dest='copy',
                        help='Copy renamed PDFs to specified folder.')

    parser.add_argument('--template-folder', '-t', dest='template_folder',
                        default=pkg_resources.resource_filename('invoice2data', 'templates'),
                        help='Folder containing invoice templates in yml file. Required.')

    parser.add_argument('input_files', type=argparse.FileType('r'), nargs='+',
                        help='File or directory to analyze.')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    output = []
    templates = read_templates(args.template_folder)
    for f in args.input_files:
        res = extract_data(f.name, templates=templates)
        if res:
            print(res)
            output.append(res)
            if args.copy:
                filename = FILENAME.format(
                    date=res['date'].strftime('%Y-%m-%d'),
                    desc=res['desc'])
                shutil.copyfile(f.name, join(args.copy, filename))
    invoices_to_csv(output, 'invoices-output.csv')

if __name__ == '__main__':
    main()

