# Data extractor for PDF invoices - invoice2data

[![Circle CI](https://circleci.com/gh/invoice-x/invoice2data.svg?style=svg)](https://circleci.com/gh/invoice-x/invoice2data)

This project has been selected for [GSoC 2018](https://developers.google.com/open-source/gsoc/). Read more [here](https://wiki.debian.org/SummerOfCode2018/Projects/ExtractingDataFromPDFInvoicesAndBillsDetails).

A modular Python library to support your accounting process. Tested on Python 2.7 and 3.4+. Main steps:

1. extracts text from PDF files using different techniques, like `pdftotext`, `pdfminer` or `tesseract` OCR.
2. searches for regex in the result using a YAML-based template system
3. saves results as CSV, JSON or XML or renames PDF files to match the content.

With the flexible template system you can:

- precisely match content PDF files
- define static fields that are the same for every invoice
- define custom fields needed in your organisation or process
- have multiple regex per field (if layout or wording changes)
- define currency
- extract invoice-items using the `lines`-plugin developed by [Holger Brunn](https://github.com/hbrunn)

Go from PDF files to this:

```
{'date': (2014, 5, 7), 'invoice_number': '30064443', 'amount': 34.73, 'desc': 'Invoice 30064443 from QualityHosting', 'lines': [{'price': 42.0, 'desc': u'Small Business StandardExchange 2010\nGrundgeb\xfchr pro Einheit\nDienst: OUDJQ_office\n01.05.14-31.05.14\n', 'pos': u'7', 'qty': 1.0}]}
{'date': (2014, 6, 4), 'invoice_number': 'EUVINS1-OF5-DE-120725895', 'amount': 35.24, 'desc': 'Invoice EUVINS1-OF5-DE-120725895 from Amazon EU'}
{'date': (2014, 8, 3), 'invoice_number': '42183017', 'amount': 4.11, 'desc': 'Invoice 42183017 from Amazon Web Services'}
{'date': (2015, 1, 28), 'invoice_number': '12429647', 'amount': 101.0, 'desc': 'Invoice 12429647 from Envato'}
```

## Installation

1. Install pdftotext

If possible get the latest [xpdf/poppler-utils](https://poppler.freedesktop.org/) version. It's included with macOS Homebrew, Debian and Ubuntu. Without it, `pdftotext` won't parse tables in PDF correctly.

2. Install `invoice2data` using pip

```
pip install invoice2data
```

## Usage

Basic usage. Process PDF files and write result to CSV.
- `invoice2data invoice.pdf`
- `invoice2data *.pdf`

Choose any of the following three input readers:
 * pdftotext `invoice2data --input-reader pdftotext invoice.pdf`
 * tesseract `invoice2data --input-reader tesseract invoice.pdf`
 * pdf miner `invoice2data --input-reader pdfminer invoice.pdf`
 
Choose any of the following output formats:
 * csv `invoice2data --output-format csv invoice.pdf`
 * json `invoice2data --output-format json invoice.pdf`
 * xml `invoice2data --output-format xml invoice.pdf`  
 
Save output file with custom name or a specific folder
`invoice2data --output-format csv --output-name myinvoices/invoices.csv invoice.pdf`

**Note:** You must specify the `output-format` in order to create `output-name`
 
Specify folder with yml templates. (e.g. your suppliers)
`invoice2data --template-folder ACME-templates invoice.pdf`

Only use your own templates and exclude built-ins
`invoice2data --exclude-built-in-templates --template-folder ACME-templates invoice.pdf`

Processes a folder of invoices and copies renamed invoices to new folder.
`invoice2data --copy new_folder folder_with_invoices/*.pdf`

Processes a single file and dumps whole file for debugging (useful when adding new templates in templates.py)
`invoice2data --debug my_invoice.pdf`

Recognize test invoices:
`invoice2data invoice2data/test/pdfs/* --debug`

If you want to use it as a lib just do

```
from invoice2data import extract_data

result = extract_data('path/to/my/file.pdf')
```

## Template system

See `invoice2data/templates` for existing templates. Just extend the list to add your own. If deployed by a bigger organisation, there should be an interface to edit templates for new suppliers. 80-20 rule. For a short tutorial on how to add new templates, see [TUTORIAL.md](TUTORIAL.md).

Templates are based on Yaml. They define one or more keywords to find the right template and regexp for fields to be extracted. They could also be a static value, like the full company name.

Template files are tried in alphabetical order.

We may extend them to feature options to be used during invoice processing.

Example:

```
issuer: Amazon Web Services, Inc.
keywords:
- Amazon Web Services
fields:
  amount: TOTAL AMOUNT DUE ON.*\$(\d+\.\d+)
  amount_untaxed: TOTAL AMOUNT DUE ON.*\$(\d+\.\d+)
  date: Invoice Date:\s+([a-zA-Z]+ \d+ , \d+)
  invoice_number: Invoice Number:\s+(\d+)
  partner_name: (Amazon Web Services, Inc\.)
options:
  remove_whitespace: false
  currency: HKD
  date_formats:
    - '%d/%m/%Y'
lines:
    start: Detail
    end: \* May include estimated US sales tax
    first_line: ^    (?P<description>\w+.*)\$(?P<price_unit>\d+\.\d+)
    line: (.*)\$(\d+\.\d+)
    last_line: VAT \*\*
```

## Development
If you are interested in improving this project, have a look at our [developer guide](DEVELOP.md) to get you started quickly.

## Roadmap and open tasks

- integrate with online OCR?
- try to 'guess' parameters for new invoice formats.
- can apply machine learning to guess new parameters?

## Maintainers
- [Manuel Riel](https://github.com/m3nu)
- [Alexis de Lattre](https://github.com/alexis-via)

## Contributors
- [Harshit Joshi](https://github.com/duskybomb): As Google Summer of Code student.
- [Holger Brunn](https://github.com/hbrunn): Add support for parsing invoice items.

## Related Projects
 * [OCR-Invoice](https://github.com/robela/OCR-Invoice) (FOSS | C#)
 * [Docparser](https://docparser.com/) (Commercial | Web Service)
 * [A-PDF](http://www.a-pdf.com/data-extractor/index.htm) (Commercial)
 * [PDFdeconstruct](http://www.glyphandcog.com/PDFdeconstruct.html?g6) (Commercial)
 * [CVision](http://www.cvisiontech.com/library/document-automation/forms-processing/extract-data-from-invoice.html) (Commercial) 
    
