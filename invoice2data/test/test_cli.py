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
from invoice2data.main import *
from invoice2data.extract.loader import read_templates

from .common import *


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.templates = read_templates()
        self.parser = create_parser()

    def compare_json_content(self, test_file, json_file):
        with open(test_file) as json_test_file, open(json_file) as json_json_file:
            jdatatest = json.load(json_test_file)
            jdatajson = json.load(json_json_file)
        # logger.info(jdatajson)
        # logger.info(jdatatest)
        if jdatajson == jdatatest:
            logger.info("True")
            return True
        else:
            logger.info("False")
            return False

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
        self.assertTrue(True)

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


if __name__ == '__main__':
    unittest.main()
