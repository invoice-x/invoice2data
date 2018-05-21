# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from os import path
import sys

setup(
    name='invoice2data',
    version='0.2.89',
    author='Manuel Riel',
    author_email='github@snapdragon.cc',
    url='https://github.com/m3nu/invoice2data',
    description='Python parser to extract data from pdf invoice',
    license="MIT",
    long_description=open(path.join(path.dirname(__file__), 'README.md')).read(),
    package_data = {
        'invoice2data.extract': [
            'templates/com/*.yml',
            'templates/de/*.yml',
            'templates/es/*.yml',
            'templates/fr/*.yml',
            'templates/nl/*.yml',
            'templates/ch/*.yml'],
        'invoice2data.test': ['pdfs/*.pdf']
        },
    packages=find_packages(),
    install_requires=[
        r.strip() for r in open(
            path.join(path.dirname(__file__), 'requirements.txt')
                ).read().splitlines() if not r.startswith('#')
        ],
    zip_safe=False,
    entry_points = {
              'console_scripts': [
                  'invoice2data = invoice2data.main:main',
              ],
          },
)
