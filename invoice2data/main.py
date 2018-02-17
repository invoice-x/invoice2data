#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import shutil
import os
from os.path import join
import logging

import invoice2data.input.pdftotext as pdftotext
import invoice2data.input.pdfminer as pdfminer
import invoice2data.input.tesseract as tesseract

from invoice2data.extract.loader import read_templates

import invoice2data.output.to_csv as output_csv
import invoice2data.output.to_json as output_json
import invoice2data.output.to_xml as output_xml

logger = logging.getLogger(__name__)

FILENAME = "{date} {desc}.pdf"

def extract_data(invoicefile, templates=None, input_module=pdftotext):
    if templates is None:
        templates = read_templates()

    extracted_str = input_module.to_text(invoicefile).decode('utf-8')

    logger.debug('START pdftotext result ===========================')
    logger.debug(extracted_str)
    logger.debug('END pdftotext result =============================')

    logger.debug('Testing {} template files'.format(len(templates)))
    for t in templates:
        optimized_str = t.prepare_input(extracted_str)

        if t.matches_input(optimized_str):
            return t.extract(optimized_str)

    logger.error('No template for %s', invoicefile)
    return False

def main():
    "Take folder or single file and analyze each."

    parser = argparse.ArgumentParser(description='Extract structured data from PDF files and save to CSV or JSON.')

    input_mapping = {
        'pdftotext': pdftotext,
        'tesseract': tesseract,
        'pdfminer': pdfminer,
        }
    parser.add_argument('--input-reader', choices=input_mapping.keys(),
                        default='pdftotext', help='Choose text extraction function. Default: pdftotext')

    output_mapping = {
        'csv': output_csv,
        'json': output_json,
        'xml': output_xml,
        'none': None
        }
    parser.add_argument('--output-format', choices=output_mapping.keys(),
                        default='none', help='Choose output format. Default: none')

    parser.add_argument('--output-name', '-o', dest='output_name', default='invoices-output',
                        help='Custom name for output file. Extension is added based on chosen format.')

    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Enable debug information.')

    parser.add_argument('--copy', '-c', dest='copy',
                        help='Copy renamed PDFs to specified folder.')

    parser.add_argument('--template-folder', '-t', dest='template_folder',
                        help='Folder containing invoice templates in yml file. Always adds built-in templates.')
    
    parser.add_argument('--exclude-built-in-templates', dest='exclude_built_in_templates',
                        default=False, help='Ignore built-in templates.', action="store_true")

    parser.add_argument('input_files', type=argparse.FileType('r'), nargs='+',
                        help='File or directory to analyze.')


    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    input_module = input_mapping[args.input_reader]
    output_module = output_mapping[args.output_format]

    templates = []
    
    # Load templates from external folder if set.
    if args.template_folder:
        templates += read_templates(os.path.abspath(args.template_folder))

    # Load internal templates, if not disabled.
    if not args.exclude_built_in_templates:
        templates += read_templates()
    
    output = []
    for f in args.input_files:
        res = extract_data(f.name, templates=templates, input_module=input_module)
        if res:
            logger.info(res)
            output.append(res)
            if args.copy:
                filename = FILENAME.format(
                    date=res['date'].strftime('%Y-%m-%d'),
                    desc=res['desc'])
                shutil.copyfile(f.name, join(args.copy, filename))

    if output_module is not None:
        output_module.write_to_file(output, args.output_name)

if __name__ == '__main__':
    main()

