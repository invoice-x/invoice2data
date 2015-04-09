# Data extractor for PDF invoices

I wrote this package to support my accounting process.

- extracts text from PDF files with `pdftotext`
- searches for regex in the result
- saves results as CSV and optionally renames PDF files to match the content

## Installation

Optionally this uses `pdfminer`, but `pdftotext` works better. You can choose which module to use. No special Python packages are necessary at the moment, except for `pdftotext`.

## Usage

Processes a folder of invoices and copies renamed invoices to new folder.
`python -m invoice2data.main folder_with_invoices --copy new_folder`

Processes a single file and dumps whole file for debugging (useful when adding new templates in templates.py)
`python -m invoice2data.main --debug my_invoice.pdf`

## Template system

See `invoice2data/templates.py` for existing templates. Just extend the list to add your own.

## Roadmap

Currently this is a proof of concept. If you scan your invoices, this could easily be connected to an OCR system. Biggest weakness is the need to manually enter new regexes. I don't see an easy way to make it "learn" new patterns.

Planned features:

- 