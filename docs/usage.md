# Usage

Basic usage — process PDF files and write the result to CSV:

```bash
invoice2data invoice.pdf
invoice2data invoice.txt
invoice2data *.pdf
```

The full list of options is in the command-line reference at the bottom of this
page (or run `invoice2data --help`).

## Input readers

invoice2data picks a backend automatically (a cascade — see {doc}`how-it-works`),
or you can force one with `--input-reader`:

```bash
invoice2data --input-reader pdfium invoice.pdf       # default, no system deps
invoice2data --input-reader pdftotext invoice.pdf    # layout-preserving (poppler)
invoice2data --input-reader text invoice.txt
invoice2data --input-reader pdfminer invoice.pdf
invoice2data --input-reader pdfplumber invoice.pdf
invoice2data --input-reader tesseract invoice.pdf    # OCR
invoice2data --input-reader ocrmypdf invoice.pdf     # OCR
invoice2data --input-reader doctr invoice.pdf        # local deep-learning OCR
invoice2data --input-reader paddleocr invoice.pdf    # local deep-learning OCR
invoice2data --input-reader gvision invoice.pdf      # Google Cloud Vision
```

See {doc}`installation` for the extras each backend needs.

- **gvision** needs the `GOOGLE_APPLICATION_CREDENTIALS` env var and a Google Cloud
  bucket name (the `GOOGLE_CLOUD_BUCKET_NAME` env var, or the `to_text` argument).
- **ocrmypdf** can clean noisy scans: any
  [OCRmyPDF option](https://ocrmypdf.readthedocs.io/) (`deskew`, `clean`,
  `rotate_pages`, `optimize`, ...) is forwarded to `ocrmypdf.ocr`. As a library,
  `invoice2data.input.ocrmypdf.pre_process_pdf(path, pre_conf=...)` returns the
  path to the cleaned, OCR-layered (usually smaller) PDF.

## Output

```bash
invoice2data --output-format csv invoice.pdf
invoice2data --output-format json invoice.pdf
invoice2data --output-format xml invoice.pdf
```

Write to a custom name or folder (you must set `--output-format` to create an
`--output-name`):

```bash
invoice2data --output-format csv --output-name myinvoices/invoices.csv invoice.pdf
```

Stream to a standard stream instead of a file with `--output-name -` (or
`/dev/stdout`, `/dev/stderr`) — logs go to stderr, so stdout stays clean for
piping:

```bash
invoice2data --output-format json --output-name - invoice.pdf | jq .
```

## Templates

```bash
invoice2data --template-folder ACME-templates invoice.pdf                          # add your own
invoice2data --exclude-built-in-templates --template-folder ACME-templates *.pdf   # only yours
```

See {doc}`tutorial` for writing templates.

## Renaming / sorting files

Process a folder of invoices and copy renamed invoices to a new folder:

```bash
invoice2data --copy new_folder folder_with_invoices/*.pdf
```

## Debugging templates

```bash
invoice2data --debug my_invoice.pdf                 # dump the full debug output
invoice2data --debug-optimized-str my_invoice.pdf   # just the matched text
invoice2data --no-color my_invoice.pdf              # disable colored logs (or NO_COLOR=1)
```

For automation pipelines, emit machine-readable JSON logs (one object per line,
on stderr) and combine with `--output-name -`:

```bash
invoice2data --in-automation --output-format json --output-name - my_invoice.pdf
```

## Generating templates & AI

Draft a new template from a sample document. The builder suggests fields/regexes
from detected dates, amounts and IBAN/VAT/BIC, **and from common labels** — it
recognises `label: value` pairs with multilingual synonyms (e.g. `BTW`/`VAT`,
`KvK`/`CoC`/`Chamber of Commerce`, `Invoice No`/`Factuurnummer`), which lets it
identify label-only fields like the Chamber-of-Commerce number (just digits) and
anchor each regex on its label. It previews what each field captures, then writes
a `.yml` after you confirm:

```bash
invoice2data --new-template sample.pdf
invoice2data --new-template sample.pdf --ai            # draft with a configured LLM instead
invoice2data --new-template sample.pdf --interactive   # review/edit each field via prompts
```

With `--interactive`, the builder walks you through each drafted field — showing
what it captures (after cleanup) and letting you keep, edit the regex, or skip it
— then offers to add fields it didn't detect. Captured values are cleaned up
automatically where useful: a VAT id keeps its dots in the capture but strips them
on output (`NL12.34.56.789.B01` → `NL123456789B01`), and a Chamber-of-Commerce
number drops an appended place name (`12345678 Amsterdam` → `12345678`).

As a last resort, let an LLM extract fields when **no template matches**:

```bash
invoice2data --ai-fallback invoice.pdf
```

Both AI paths are opt-in and configured via `INVOICE2DATA_AI_*` — see {doc}`ai`.

## Use as a Python library

```python
from invoice2data import extract_data

result = extract_data("path/to/my/file.pdf")
```

With your own templates:

```python
from invoice2data import extract_data
from invoice2data.extract.loader import read_templates

templates = read_templates("/path/to/your/templates/")
result = extract_data(filename, templates=templates)
```

Loading templates from a string (e.g. a database column or an API response)
instead of from disk, with `ordered_load`:

```python
import yaml
from invoice2data import extract_data
from invoice2data.extract.loader import ordered_load

templates = ordered_load(db_json_string)                          # JSON (default)
templates = ordered_load(db_yaml_string, loader=yaml.safe_load)   # or YAML
result = extract_data(filename, templates=templates)
```

By default `extract_data` returns `{}` when nothing matches. Pass
`raise_on_error=True` to get a typed `InvoiceProcessingError`
(`RequiredFieldsMissingError` / `NoTemplateFoundError`) instead — see the
{doc}`reference` for the full library API.

## Command-line reference

```{eval-rst}
.. click:: invoice2data.__main__:main
    :prog: invoice2data
    :nested: full
```
