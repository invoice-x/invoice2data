# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from os import path


def readme_description():
    with open(path.join(path.dirname(__file__), 'README.rst'), "rb") as readme_file:
        return readme_file.read().decode('utf-8')


setup(
    name='invoice2data',
    version='0.3.2',
    author='Manuel Riel',
    author_email='github@snapdragon.cc',
    url='https://github.com/m3nu/invoice2data',
    description='Python parser to extract data from pdf invoice',
    license="MIT",
    long_description=readme_description(),
    package_data={
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
    entry_points={
        'console_scripts': [
            'invoice2data = invoice2data.main:main',
        ],
    },
)
