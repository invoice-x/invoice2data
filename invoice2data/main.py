#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import argparse
import shutil
from os import listdir
from os.path import isfile, isdir, join

import dateparser
import pkg_resources
import invoice2data.pdftotext as pdftotext
import invoice2data.image_to_text as image_to_text
from invoice2data.templates import read_templates
from invoice2data.output import invoices_to_csv
import logging

logger = logging.getLogger(__name__)

FILENAME = "{date} {desc}.pdf"

def extract_data(invoicefile, templates, debug=False):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    output = {}
    extracted_str = pdftotext.to_text(invoicefile).decode('utf-8')

    # Try OCR, when we get an almost empty str.
    charcount = len(extracted_str)
    logger.debug('number of char in pdf2text extract: %d', charcount)
    if charcount < 40:
        logger.debug('Starting OCR')
        extracted_str = image_to_text.to_text(invoicefile)
    logger.debug(extracted_str)

    logger.debug('Testing {} template files'.format(len(templates)))
    for t in templates:
        if all([keyword in extracted_str for keyword in t['keywords']]):
            logger.debug("keywords=%s", t['keywords'])
            for k, v in t['fields'].items():
                if k.startswith('static_'):
                    logger.debug("field=%s | static value=%s", k, v)
                    output[k.replace('static_', '')] = v
                else:
                    logger.debug("field=%s | regexp=%s", k, v)
                    res_find = re.findall(v, extracted_str)
                    if res_find:
                        if k.startswith('date'):
                            raw_date = res_find[0]
                            output[k] = dateparser.parse(raw_date)
                            logger.debug("res_find=%s", output[k])
                        elif k.startswith('amount'):
                            output[k] = float(
                                res_find[0].replace(',', '.').replace(' ', ''))
                        else:
                            output[k] = res_find[0]
                            logger.debug("res_find=%s", res_find)

            output['desc'] = 'Invoice %s from %s' % (
                output['invoice_number'], t['keywords'][0])
            logger.debug(output)
            return output

    logger.warning('No template for %s', invoicefile)
    logger.debug(output)
    return False

def main():
    "Take folder or single file and analyze each."

    parser = argparse.ArgumentParser(description='Process some integers.')
    
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Print debug information.')
    
    parser.add_argument('--copy', dest='copy',
                        help='Copy renamed PDFs to specified folder.')
    
    parser.add_argument('--template-folder', dest='template_folder', 
                        default=pkg_resources.resource_filename('invoice2data', 'templates'),
                        help='Folder containing invoice templates in yml file. Required.')
    
    parser.add_argument('input_files', type=argparse.FileType('r'), nargs='+',
                        help='File or directory to analyze.')

    args = parser.parse_args()

    output = []
    templates = read_templates(args.template_folder)
    for f in args.input_files:
        res = extract_data(f.name, templates=templates, debug=args.debug)
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

