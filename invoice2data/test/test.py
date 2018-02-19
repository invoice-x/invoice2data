import os

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

	def _run_test_on_folder(self, folder):
		for path, subdirs, files in os.walk(folder):
			for file in files:
				return (os.path.join(path, file))

	def _debug_test_on_folder(self, folder):
		for path, subdirs, files in os.walk(folder):
			for file in files:
				logging.basicConfig(level=logging.DEBUG)
				res = extract_data(os.path.join(path, file), self.templates)
				logger.info(res)   
				print(res, files) 
	
	def test_output_format(self):
		parser = create_parser()
		arg_output = ['csv', 'json', 'xml']

		output_mapping = {
		'csv': to_csv,
		'json': to_json,
		'xml': to_xml,

		'none': None
		}

		
		for output_file in arg_output:
			folder = pkg_resources.resource_filename(__name__, 'pdfs')
			args = parser.parse_args(['--output-format',
				output_file,
				self._run_test_on_folder(folder)])
			self.assertTrue(output_mapping[args.output_format])

	def test_input(self):
		parser = create_parser()
		
		arg_input = {'pdftotext', 'tesseract', 'pdfminer'}
		input_mapping = {
		'pdftotext': pdftotext,
		'tesseract': tesseract,
		'pdfminer': pdfminer,
		}

		folder = pkg_resources.resource_filename(__name__, 'pdfs')
		
		for input_file in arg_input:
			args = parser.parse_args(['--input-reader',
				input_file,
				self._run_test_on_folder(folder)])
			self.assertTrue(input_mapping[args.input_reader])

	def test_output_name(self):
		parser = create_parser()
		folder = pkg_resources.resource_filename(__name__, 'pdfs')      
		args = parser.parse_args(['--output-name', 'inv_test',self._run_test_on_folder(folder)])
		self.assertTrue(args.output_name)

	def test_debug(self):
		parser = create_parser()
		folder = pkg_resources.resource_filename(__name__, 'pdfs')      
		args = parser.parse_args(['--debug', self._run_test_on_folder(folder)])
		self.assertTrue(args.debug)
		# For printing
		# print('\n=*==*=*=*=*=*=*=*=*=*=*=*=*=*=*=*==*=*=*==**==*=*=*=*=*=*=*=*=*=\n')
		# self._debug_test_on_folder(folder)
		# print('\n=*==*=*=*=*=*=*=*=*=*=*=*=*=*=*=*==*=*=*==**==*=*=*=*=*=*=*=*=*=\n')

	def test_copy(self):
		parser = create_parser()
		folder = pkg_resources.resource_filename(__name__, 'pdfs')      
		args = parser.parse_args(['--copy', '/invoice2data/test/',self._run_test_on_folder(folder)])
		self.assertTrue(args.copy)

	def test_template(self):
		parser = create_parser()
		folder = pkg_resources.resource_filename(__name__, 'pdfs')      
		args = parser.parse_args(['--template-folder', 'ACME-templates',self._run_test_on_folder(folder)])
		self.assertTrue(args.template_folder)

	def test_exclude_template(self):
		parser = create_parser()
		folder = pkg_resources.resource_filename(__name__, 'pdfs')      
		args = parser.parse_args(['--exclude-built-in-templates', '--template-folder', 'ACME-templates',self._run_test_on_folder(folder)])
		self.assertTrue(args.exclude_built_in_templates)
		

if __name__ == '__main__':
	unittest.main()