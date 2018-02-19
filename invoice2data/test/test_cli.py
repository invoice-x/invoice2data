import os
import glob

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