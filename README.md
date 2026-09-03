<p align="center">
  <img src="docs/_static/banner.svg" alt="invoice2data" width="640">
</p>

# Data extractor for PDF invoices - invoice2data

[![Read the documentation at https://invoice2data.readthedocs.io/](https://img.shields.io/readthedocs/invoice2data/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Version](https://img.shields.io/pypi/v/invoice2data.svg)](https://pypi.python.org/pypi/invoice2data)
[![Support Python versions](https://img.shields.io/pypi/pyversions/invoice2data.svg)](https://pypi.python.org/pypi/invoice2data)
[![License](https://img.shields.io/pypi/l/invoice2data)][license]
[![Tests](https://github.com/invoice-x/invoice2data/workflows/Tests/badge.svg)][tests]
[![Coverage](https://raw.githubusercontent.com/invoice-x/invoice2data/python-coverage-comment-action-data/badge.svg)][coverage]
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

<!-- docs-body -->

[pypi status]: https://pypi.org/project/invoice2data/
[read the docs]: https://invoice2data.readthedocs.io/
[tests]: https://github.com/invoice-x/invoice2data/actions?workflow=Tests
[coverage]: https://github.com/invoice-x/invoice2data/actions?workflow=Tests
[pre-commit]: https://github.com/pre-commit/pre-commit
[ruff badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff project]: https://github.com/charliermarsh/ruff

A command line tool and Python library that automates the extraction of key information from invoices to support your accounting
process. The library is very flexible and can be used on other types of business documents as well.

In essence, invoice2data simplifies getting data from invoices by:

- **Automating text extraction** — no more manual copying and pasting.
- **Using templates for structure** — handles different invoice layouts.
- **Providing structured output** — data ready for analysis or further processing.

This makes it a valuable tool for businesses and developers dealing with a large
volume of invoices, saving time and reducing manual-entry errors. It:

1. extracts text from PDF files with a pluggable, cascading backend —
   `pdfium` (default, no system deps), `pdftotext`, `text`, `pdfminer`,
   `pdfplumber`, or OCR (`tesseract`, `ocrmypdf`, `docTR`, `paddleocr`,
   `gvision`).
2. searches for regex in the result using a YAML or JSON-based template system
   (with an optional [AI fallback](https://invoice2data.readthedocs.io/en/latest/ai.html)).
3. saves results as CSV, JSON or XML, or renames PDF files to match the content.

With the flexible template system you can:

- precisely match content PDF files
- plugins available to match line items and tables
- define static fields that are the same for every invoice
- define custom fields needed in your organisation or process
- have multiple regex per field (if layout or wording changes)
- define currency
- extract invoice-items using the `lines`-plugin developed by [Holger
  Brunn](https://github.com/hbrunn)

Go from PDF files to this:

    {'issuer': 'QualityHosting', 'amount': 34.73, 'date': datetime.datetime(2014, 5, 7, 0, 0), 'invoice_number': '30064443', 'currency': 'EUR', 'desc': 'Invoice 30064443 from QualityHosting', 'template_name': 'com.qualityhosting.yml'}
    {'issuer': 'Amazon EU', 'amount': 35.24, 'date': datetime.datetime(2014, 6, 4, 0, 0), 'invoice_number': 'EUVINS1-OF5-DE-120725895', 'currency': 'EUR', 'desc': 'Invoice EUVINS1-OF5-DE-120725895 from Amazon EU'}
    {'issuer': 'Amazon Web Services', 'amount': 4.11, 'date': datetime.datetime(2014, 8, 3, 0, 0), 'invoice_number': '42183017', 'currency': 'USD', 'desc': 'Invoice 42183017 from Amazon Web Services'}
    {'issuer': 'Envato', 'amount': 101.0, 'date': datetime.datetime(2015, 1, 28, 0, 0), 'invoice_number': '12429647', 'currency': 'USD', 'desc': 'Invoice 12429647 from Envato'}


## Quickstart

```bash
pip install invoice2data
invoice2data invoice.pdf                          # extract -> CSV
invoice2data --output-format json invoice.pdf     # or JSON / XML
```

As a Python library:

```python
from invoice2data import extract_data

result = extract_data("invoice.pdf")
```

No system libraries are required by default — the `pdfium` backend bundles its own
engine. Optional backends and extras (poppler, OCR, AI, ...) are covered in the
[installation guide][installation].

## Documentation

Full documentation: **<https://invoice2data.readthedocs.io/>**

- [How it works][how-it-works] — the extraction pipeline
- [Installation][installation] — backends, OCR and optional extras
- [Usage][usage] — all CLI options and common tasks
- [Template creation][tutorial] — write templates for your invoices
- [Recommended fields][fields] — the canonical output schema
- [AI features][ai] — optional LLM fallback & template generation
- [FAQ][faq] — including a comparison with other tools

## Development

If you are interested in improving this project, have a look at our
[contributor guide] to get you started quickly.

## Roadmap and open tasks

Everything that used to live here has shipped:

- online OCR — Google [Cloud Vision][gvision], plus local DL backends [docTR][doctr] and [PaddleOCR][paddleocr]
- guess parameters for new invoice formats — `invoice2data --new-template SAMPLE` (deterministic, no AI needed)
- ML-assisted template creation — `invoice2data --new-template SAMPLE --ai` (AI-1) and runtime `--ai-fallback` (AI-2); see the [AI features][ai] page
- per-field data cleanup — the `replace:` key on each field
- advanced table parsing — opt-in [Camelot][camelot] plugin (`pip install invoice2data[camelot]`), plus an [Excalibur → template converter][usage-excalibur]

Currently open on the tracker:

- **Non-invoice document schemas** (waybills, delivery notes, purchase orders): the
  per-template `required_fields:` override lets a template opt out of the
  invoice-shaped default today, but canonical schemas for other document
  types are still deferred.
- **Visual template builder in Odoo** — community-driven via [OCA/edi][odoo-oca-edi]
  (`account_invoice_import_invoice2data_db_templates`, in review). Wraps the
  authoring APIs listed above in a click-to-suggest UI on top of the disk
  templates.
- Tighter identifier validators via [python-stdnum][python-stdnum] — deferred
  pending Odoo core's stdnum version alignment.

Issues and pull requests welcome on any of these.

[gvision]: https://cloud.google.com/vision
[doctr]: https://github.com/mindee/doctr
[paddleocr]: https://github.com/PaddlePaddle/PaddleOCR
[camelot]: https://github.com/camelot-dev/camelot
[usage-excalibur]: https://invoice2data.readthedocs.io/en/latest/usage.html
[odoo-oca-edi]: https://github.com/OCA/edi
[python-stdnum]: https://arthurdejong.org/python-stdnum/

## Maintainers

- [Manuel Riel](https://github.com/m3nu)
- [Alexis de Lattre](https://github.com/alexis-via)
- [bosd](https://github.com/bosd)

## Contributors and Credits

- [Harshit Joshi](https://github.com/duskybomb): As Google Summer of
  Code student.
- [Holger Brunn](https://github.com/hbrunn): Add support for parsing
  invoice items.

[pypi]: https://pypi.org/
[file an issue]: https://github.com/invoice-x/invoice2data/issues
[pip]: https://pip.pypa.io/

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## Used By

- Odoo, OCA module [account_invoice_import_invoice2data](https://github.com/OCA/edi)

## Related Projects

- [OCR-Invoice](https://github.com/robela/OCR-Invoice) (FOSS \| C\#)
- [DeepLogic AI](https://deeplogicai.tech/case_list/automatic-key-information-extraction-business-documents/) (Commercial \| SaaS)
- [Docparser](https://docparser.com/) (Commercial \| Web Service)
- [A-PDF](http://www.a-pdf.com/data-extractor/index.htm) (Commercial)
- [PDFdeconstruct](http://www.glyphandcog.com/PDFdeconstruct.html?g6)
  (Commercial)
- [CVision](http://www.cvisiontech.com/library/document-automation/forms-processing/extract-data-from-invoice.html)
  (Commercial)

<!-- github-only -->

[license]: https://invoice2data.readthedocs.io/latest/license.html
[contributor guide]: https://invoice2data.readthedocs.io/latest/contributing.html
[command-line reference]: https://invoice2data.readthedocs.io/latest/usage.html
[tutorial]: https://invoice2data.readthedocs.io/latest/tutorial.html
[installation]: https://invoice2data.readthedocs.io/latest/installation.html
[how-it-works]: https://invoice2data.readthedocs.io/latest/how-it-works.html
[usage]: https://invoice2data.readthedocs.io/latest/usage.html
[fields]: https://invoice2data.readthedocs.io/latest/recommended-template-fields.html
[ai]: https://invoice2data.readthedocs.io/latest/ai.html
[faq]: https://invoice2data.readthedocs.io/latest/faq.html
