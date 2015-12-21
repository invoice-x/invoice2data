#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import re
import argparse
import shutil
from os import listdir
from os.path import isfile, isdir, join

from .date_parser import str2date
import pdftotext
import image_to_text
from .templates import templates
from .output import invoices_to_csv

FILENAME = "{date} {desc}.pdf"

def extract_data(file, debug=True):
    output = {}
    str = pdftotext.to_text(file)

    # Try OCR, when we get an almost empty str.
    if len(str) < 10:
        str = image_to_text.to_text(file)
    if debug: print(str)

    for t in templates:
        if t['keyword'] in str:
            for k, v in t['data']:
                if debug: print("regexp=%s"% v)
                res_find = re.findall(v, str)
                if debug: print("res_find=%s" % res_find)
                if k.startswith('date'):
                    raw_date = res_find[0]
                    output[k] = str2date(raw_date)
                elif k.startswith('amount'):
                    output[k] = float(res_find[0].replace(',', '.'))
                else:
                    output[k] = res_find[0]

            output['desc'] = 'Invoice %s from %s' % (output['invoice_number'], t['keyword'])
            if debug: print(output)
            return output
    
    print('No template for %s' % file)
    if debug: print(output)
    return False

if __name__ == '__main__':
    "Take folder or single file and analyze each."

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--debug', dest='debug', action='store_true',
                       help='Print PDF text to command line.')
    parser.add_argument('--copy', dest='copy',
                       help='Copy renamed PDFs to specified folder.')
    parser.add_argument('file_folder',
                       help='File or directory to analyze.')
    args = parser.parse_args()

    if isfile(args.file_folder):
        extract_data(args.file_folder)
    elif isdir(args.file_folder):
        onlyfiles = [ f for f in listdir(args.file_folder) if isfile(join(args.file_folder, f)) ]
        output = []
        for f in onlyfiles:
            try:
                res = extract_data(join(args.file_folder, f))
                if res:
                    output.append(res)
                    if args.copy:
                        filename = FILENAME.format(date=res['date'].strftime('%Y-%m-%d'), desc=res['desc'])
                        shutil.copyfile(join(args.file_folder, f), join(args.copy, filename))
                else:
                    if args.copy:
                        shutil.copyfile(join(args.file_folder, f), join(args.copy, f))
            except KeyboardInterrupt:
                print('Error with %s' % f)

        invoices_to_csv(output, 'invoices-output.csv')

 




