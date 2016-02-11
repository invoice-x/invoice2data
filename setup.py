# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import sys

if sys.version_info[0] == 2:
    pdfminer = "pdfminer"
elif sys.version_info[0] == 3:
    pdfminer = "pdfminer3k"

version = open('VERSION').read().strip()

setup(
    name='invoice2data',
    version=version,
    author='Manuel Riel',
    author_email='github@snapdragon.cc',
    url='https://github.com/manuelRiel/invoice2data',
    description='Python parser to extract data from pdf invoice',
    license="MIT",
    long_description=open('README.md').read(),
    package_data = {
        'invoice2data': ['templates/*.yml', 'templates/fr/*.yml'],
        'invoice2data.test': ['pdfs/*.pdf']
        },
    packages=find_packages(),
    install_requires=[
        r.strip() for r in open('requirements.txt').read().splitlines(),
        pdfminer,
        ],
    zip_safe=False,
    entry_points = {
              'console_scripts': [
                  'invoice2data = invoice2data.main:main',                  
              ],              
          },
)
