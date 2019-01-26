import datetime
import os
import glob
import filecmp
import json
import shutil

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import unittest

import pkg_resources
from invoice2data.main import create_parser, main
from invoice2data.extract.loader import read_templates

from .common import get_sample_files


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.templates = read_templates()
        self.parser = create_parser()

    def compare_json_content(self, test_file, json_file):
        with open(test_file) as json_test_file, open(json_file) as json_json_file:
            jdatatest = json.load(json_test_file)
            jdatajson = json.load(json_json_file)
            return jdatajson == jdatatest

    def test_input(self):
        args = self.parser.parse_args(['--input-reader', 'pdftotext'] + get_sample_files('.pdf'))
        main(args)

    def test_output_name(self):
        test_file = 'inv_test_8asd89f78a9df.csv'
        args = self.parser.parse_args(['--output-name', test_file, '--output-format', 'csv']
                                      + get_sample_files('.pdf'))
        main(args)
        self.assertTrue(os.path.exists(test_file))
        os.remove(test_file)

    def test_debug(self):
        args = self.parser.parse_args(['--debug'] + get_sample_files('.pdf'))
        main(args)

    # TODO: move result comparison to own test module.
    # TODO: parse output files instaed of comparing them byte-by-byte.

    def test_content_json(self):
        pdf_files = get_sample_files('.pdf')
        json_files = get_sample_files('.json')
        test_files = 'test_compare.json'
        for pfile in pdf_files:
            for jfile in json_files:
                if pfile[:-4] == jfile[:-5]:
                    args = self.parser.parse_args(
                        ['--output-name', test_files, '--output-format', 'json', pfile])
                    main(args)
                    compare_verified = self.compare_json_content(test_files, jfile)
                    print(compare_verified)
                    if not compare_verified:
                        self.assertTrue(False)
                    os.remove(test_files)

    def test_copy(self):
        # folder = pkg_resources.resource_filename(__name__, 'pdfs')
        directory = os.path.dirname("invoice2data/test/copy_test/pdf/")
        os.makedirs(directory)
        args = self.parser.parse_args(['--copy', 'invoice2data/test/copy_test/pdf'] + get_sample_files('.pdf'))
        main(args)
        i = 0
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'copy_test/pdf')):
            for file in files:
                if file.endswith(".pdf"):
                    i += 1

        shutil.rmtree('invoice2data/test/copy_test/', ignore_errors=True)
        self.assertEqual(i, len(get_sample_files('.json')))
        '''
        if i != len(self._get_test_file_json_path()):
            print(i)
            self.assertTrue(True)
        else:
            print(i)
            self.assertTrue(False, "Number of files not equal")
        '''

    # def test_template(self):
    #     directory = os.path.dirname("invoice2data/test/temp_test/")
    #     os.makedirs(directory)
    #     args = self.parser.parse_args(['--template-folder', 'ACME-templates', self._get_test_file_path()])
    #     main(args)
    #     shutil.rmtree('invoice2data/test/temp_test/', ignore_errors=True)
    #     self.assertTrue(args.template_folder)

    def test_exclude_template(self):
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
            for file in files:
                if file.endswith("oyo.pdf"):
                    my_file = os.path.join(path, file)
        directory = os.path.dirname("invoice2data/test/temp_test/")
        os.makedirs(directory)
        shutil.copy('invoice2data/extract/templates/com/com.oyo.invoice.yml', 'invoice2data/test/temp_test/')
        args = self.parser.parse_args(['--exclude-built-in-templates',
                                       '--template-folder',
                                       directory,
                                       my_file])
        main(args)
        shutil.rmtree('invoice2data/test/temp_test/')

    def get_filename_format_test_data(self, filename_format):
        # Generate test input and expected output by walking the compare dir
        data = {}
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
            for file in files:
                root, ext = os.path.splitext(file)
                if root not in data:
                    data[root] = {}
                if file.endswith('.pdf'):
                    data[root]['input_fpath'] = os.path.join(path, file)
                if file.endswith('.json'):
                    with open(os.path.join(path, file), 'r') as f:
                        res = json.load(f)[0]
                        date = datetime.datetime.strptime(res['date'], '%d/%m/%Y')
                        data[root]['output_fname'] = filename_format.format(
                            date=date.strftime('%Y-%m-%d'),
                            invoice_number=res['invoice_number'],
                            desc=res['desc']
                        )
        return data

    def test_copy_with_default_filename_format(self):
        copy_dir = os.path.join('invoice2data', 'test', 'copy_test', 'pdf')
        filename_format = "{date} {invoice_number} {desc}.pdf"

        data = self.get_filename_format_test_data(filename_format)

        os.makedirs(copy_dir)

        sample_files = [v['input_fpath'] for k,v in data.items()]

        args = self.parser.parse_args(['--copy', copy_dir] + sample_files)
        main(args)

        self.assertTrue(all(os.path.exists(os.path.join(copy_dir, v['output_fname'])) for k,v in data.items()))

        shutil.rmtree(os.path.dirname(copy_dir), ignore_errors=True)

    def test_copy_with_custom_filename_format(self):
        copy_dir = os.path.join('invoice2data', 'test', 'copy_test', 'pdf')
        filename_format = "Custom Prefix {date} {invoice_number}.pdf"

        data = self.get_filename_format_test_data(filename_format)

        os.makedirs(copy_dir)

        sample_files = [v['input_fpath'] for k,v in data.items()]

        args = self.parser.parse_args(['--copy', copy_dir, '--filename-format', filename_format] + sample_files)
        main(args)

        self.assertTrue(all(os.path.exists(os.path.join(copy_dir, v['output_fname'])) for k,v in data.items()))

        shutil.rmtree(os.path.dirname(copy_dir), ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
