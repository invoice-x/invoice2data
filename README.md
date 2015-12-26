# Data extractor for PDF invoices - invoice2data

I wrote this package to support my accounting process.

- extracts text from PDF files
- searches for regex in the result
- saves results as CSV
- optionally renames PDF files to match the content

Go from PDF files to this:

```
{'date': (2014, 5, 7), 'invoice_number': '30064443', 'amount': 34.73, 'desc': 'Invoice 30064443 from QualityHosting'}
{'date': (2014, 6, 4), 'invoice_number': 'EUVINS1-OF5-DE-120725895', 'amount': 35.24, 'desc': 'Invoice EUVINS1-OF5-DE-120725895 from Amazon EU'}
{'date': (2014, 8, 3), 'invoice_number': '42183017', 'amount': 4.11, 'desc': 'Invoice 42183017 from Amazon Web Services'}
{'date': (2015, 1, 28), 'invoice_number': '12429647', 'amount': 101.0, 'desc': 'Invoice 12429647 from Envato'}
```

## Installation

Install pdftotext

For ubuntu:

```
sudo apt-get install xpdf
```

Install the lib using pip

```
pip install invoice2data
```

Optionally this uses `pdfminer`, but `pdftotext` works better. You can choose which module to use. No special Python packages are necessary at the moment, except for `pdftotext`.

There is also `tesseract` integration as a fallback, if no text can be extracted. But it may be more reliable to use 

## Usage

Processes a folder of invoices and copies renamed invoices to new folder.
`python -m invoice2data.main folder_with_invoices --copy new_folder`

Processes a single file and dumps whole file for debugging (useful when adding new templates in templates.py)
`python -m invoice2data.main --debug my_invoice.pdf`

Recognize test invoices:
`python -m invoice2data.main invoice2data/test/pdfs --debug`

If you want to use it as a lib just do

```
from invoice2data import extract_data

result = extract_data('path/to/my/file.pdf')
```

## Template system

See `invoice2data/templates.py` for existing templates. Just extend the list to add your own. If deployed by a bigger organisation, there should be an interface to edit templates for new suppliers. 80-20 rule.

## Roadmap

Currently this is a proof of concept. If you scan your invoices, this could easily be connected to an OCR system. Biggest weakness is the need to manually enter new regexes. I don't see an easy way to make it "learn" new patterns.

Planned features:

- integrate with online OCR
- try to 'guess' parameters for new invoice formats
- can apply machine learning to guess new parameters?

## Contributors
- Alexis de Lattre: Add setup.py for Pypi, fix locale bug, add templates for new invoice types.
