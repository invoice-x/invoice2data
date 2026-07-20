# Quickstart

A five-minute tour: install invoice2data, run it against a PDF, understand the
result, and author your first template. See {doc}`installation` for optional
extras (OCR, camelot, AI, ...) and {doc}`tutorial` for the full template DSL.

## 1. Install

```bash
pip install invoice2data
```

That gets you the library, the `invoice2data` command, ~215 bundled community
templates, and the pure-Python `pypdfium2` backend. No system dependencies.

To add layout-preserving PDF extraction (recommended for column-aligned
invoices), also install poppler:

```bash
# Debian / Ubuntu
sudo apt install poppler-utils
# macOS (Homebrew)
brew install poppler
# Windows
choco install poppler
```

## 2. Extract from a sample invoice

```bash
invoice2data invoice.pdf
```

If one of the bundled templates matches, you get a Python-`repr`-style
dictionary on stdout with the fields the template captured — `issuer`,
`invoice_number`, `amount`, `date`, `vat`, and any `lines` /`tax_lines` the
template defined.

Write it to a file in a machine-friendly format:

```bash
invoice2data --output-format json --output-name invoice.json invoice.pdf
invoice2data --output-format json --output-name - invoice.pdf | jq .
```

## 3. Understand what happened

If no template matches you'll see `No template for <file>` on stderr. Two ways
to debug from there:

```bash
invoice2data --debug-optimized-str invoice.pdf   # show the extracted text
invoice2data --debug invoice.pdf                 # show every template it tried
```

`--debug-optimized-str` is usually enough — you look at the text the way
invoice2data sees it, then write a template that matches it.

## 4. Author your first template

The easy path: let the interactive builder draft one from your sample PDF.

```bash
invoice2data --new-template invoice.pdf --interactive
```

The builder:

1. Reads the PDF text through the default backend cascade.
2. Detects candidate fields — dates, amounts, IBAN / VAT / BIC identifiers,
   and label-value pairs (`BTW: NL...`, `Invoice No.: 4321`, ...).
3. Prompts you for each drafted field (`keep` / `edit regex` / `skip`),
   previews what it would capture, and writes an `<issuer>.yml` after you
   confirm.

To let an LLM draft the template instead (opt-in, key-gated), configure a
provider per {doc}`ai` and add `--ai`:

```bash
invoice2data --new-template invoice.pdf --ai --template-out acme.yml
```

Either way you end up with a YAML file you own. A minimal one looks like:

```yaml
issuer: ACME
keywords:
  - ACME Ltd
fields:
  invoice_number:
    parser: regex
    regex: 'Invoice\s*(?:No|#)\s*[:.]?\s*(\S+)'
  date:
    parser: regex
    regex: 'Date\s*:\s*(\d{4}-\d{2}-\d{2})'
    type: date
  amount:
    parser: regex
    regex: 'Total\s+([\d.,]+)'
    type: float
options:
  currency: EUR
  date_formats:
    - '%Y-%m-%d'
```

## 5. Use your template

Put the file under `./my-templates/` and point invoice2data at it:

```bash
invoice2data --template-folder ./my-templates invoice.pdf
```

To skip the bundled templates entirely (only your own):

```bash
invoice2data --template-folder ./my-templates --exclude-built-in-templates invoice.pdf
```

## From a Python program

```python
from invoice2data import extract_data

result = extract_data("invoice.pdf")
if result:
    print(result["amount"], result["date"])
```

Templates from your own folder:

```python
from invoice2data import extract_data
from invoice2data.extract.loader import read_templates

templates = read_templates("./my-templates")
result = extract_data("invoice.pdf", templates=templates)
```

Or from a database column / API payload:

```python
from invoice2data.extract.loader import ordered_load
templates = ordered_load(db_json_string)                          # JSON
templates = ordered_load(db_yaml_string, loader=yaml.safe_load)   # YAML
result = extract_data("invoice.pdf", templates=templates)
```

By default `extract_data` returns `{}` when nothing matches. To distinguish
"no template" from "template matched but a required field is missing", pass
`raise_on_error=True` and catch the typed
`NoTemplateFoundError` / `RequiredFieldsMissingError` — see {doc}`reference`.

## Next steps

- {doc}`usage` — CLI reference (input readers, output formats, debugging).
- {doc}`cookbook` — recipes for common gotchas (multi-page lines, currency
  symbols, streaming templates, ...).
- {doc}`tutorial` — full template authoring DSL.
- {doc}`ai` — how to configure the opt-in LLM path.
