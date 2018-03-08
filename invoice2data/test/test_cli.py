import os
import glob
import filecmp

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import unittest

import pkg_resources
from invoice2data.main import *
from invoice2data.extract.loader import read_templates

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.templates = read_templates()
        self.parser = create_parser()

    def _get_test_file_path(self):
        out_files = []
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'pdfs')):
            for file in files:
                if file.endswith(".pdf"):
                    out_files.append(os.path.join(path, file))
        return out_files

    def _get_test_file_content():
        pass

    def test_input(self):
        args = self.parser.parse_args(['--input-reader', 'pdftotext'] + self._get_test_file_path())
        main(args)

    def test_output_name(self):
        test_file = 'inv_test_8asd89f78a9df.csv'
        args = self.parser.parse_args(['--output-name', test_file, '--output-format', 'csv'] + self._get_test_file_path())
        main(args)
        self.assertTrue(os.path.exists(test_file))
        os.remove(test_file)

    def test_debug(self):
        args = self.parser.parse_args(['--debug'] + self._get_test_file_path())
        main(args)

    def test_content_csv(self):
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
            for file in files:
                if file.endswith(".csv"):
                    cmp_file = os.path.join(path, file)

        test_files = 'inv_test.csv'
        args = self.parser.parse_args(['--output-name', test_files, '--output-format', 'csv'] + self._get_test_file_path())
        main(args)
        self.assertTrue(filecmp.cmp(test_files, cmp_file, shallow=False))
        os.remove(test_files)

    def test_content_xml(self):
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
            for file in files:
                if file.endswith(".xml"):
                    cmp_file = os.path.join(path, file)

        test_files = 'inv_test.xml'
        args = self.parser.parse_args(['--output-name', test_files, '--output-format', 'xml'] + self._get_test_file_path())
        main(args)
        self.assertTrue(filecmp.cmp(test_files, cmp_file, shallow=False))
        os.remove(test_files)

    def test_content_json(self):
        for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
            for file in files:
                if file.endswith(".json"):
                    cmp_file = os.path.join(path, file)

        test_files = 'inv_test.json'
        args = self.parser.parse_args(['--output-name', test_files, '--output-format', 'json'] + self._get_test_file_path())
        main(args)
        self.assertTrue(filecmp.cmp(test_files, cmp_file, shallow=False))
        os.remove(test_files)

    # def test_content(self):
    #     folder_output = pkg_resources.resource_filename(__name__, 'outputFile')
    #     for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'pdfs')):
    #         for file in files:
    #             if file.endswith(".pdf"):
    #                 # out_files.append()
    #                 args = self.parser.parse_args(['--output-format', 'csv'] + os.path.join(path, file))
    #                 main(args)
    #                 filecmp.cmp('invoices-output')

    # def test_copy(self):
    #     parser = create_parser()
    #     folder = pkg_resources.resource_filename(__name__, 'pdfs')      
    #     args = parser.parse_args(['--copy', '/invoice2data/test/', self._get_test_file_path()])
    #     self.assertTrue(args.copy)

    # def test_template(self):
    #     parser = create_parser()
    #     folder = pkg_resources.resource_filename(__name__, 'pdfs')      
    #     args = parser.parse_args(['--template-folder', 'ACME-templates', self._get_test_file_path()])
    #     self.assertTrue(args.template_folder)

    # def test_exclude_template(self):
    #     parser = create_parser()
    #     folder = pkg_resources.resource_filename(__name__, 'pdfs')      
    #     args = parser.parse_args(['--exclude-built-in-templates', '--template-folder', 'ACME-templates', self._get_test_file_path()])
    #     self.assertTrue(args.exclude_built_in_templates)
        

if __name__ == '__main__':
    unittest.main()