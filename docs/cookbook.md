# Cookbook

Recipes for common gotchas. Each one starts with a symptom and points at the
smallest change that fixes it. For the full template DSL see {doc}`tutorial`
and {doc}`recommended-template-fields`.

## "No template matches" — first pass

Feed the raw text through the same backend the extractor uses:

```bash
invoice2data --debug-optimized-str invoice.pdf
```

Copy the shape of a line into a regex, put it in a template, iterate. Or let
the builder draft one for you:

```bash
invoice2data --new-template invoice.pdf --interactive
```

## "A template matches but the amount is empty"

Turn on the per-template debug log and see which field regexes failed:

```bash
invoice2data --debug invoice.pdf
```

Usually the fix is one of:
- The regex assumes a different separator (`.` vs `,` for thousands / decimal).
- The regex assumes a currency symbol prefix / suffix that isn't there.
- The amount is on a different line than the label (see the multi-line recipe
  below).

For the currency-symbol case, opt into `extract_number` on the field so the
first numeric token gets plucked from the wider capture:

```yaml
amount:
  parser: regex
  regex: 'Balance\s+(-?\$?[\d,]+\.\d{2})'
  type: float
  extract_number: true
```

## "Line items span multiple lines"

Bracket each item with `first_line` (the item start), `line` (continuation
lines — repeated), and `last_line` (the amounts row). Description values are
concatenated across matches:

```yaml
lines:
  first_line: '^(?P<sku>SKU\d+)\s+(?P<name>.+)$'
  line: '^\s{4,}(?P<name>\w[\w\s]*)$'
  last_line: '^\s+(?P<qty>\d+)\s+(?P<price>[\d.]+)$'
```

## "Line items span multiple pages"

Two independent tools:

1. **`end_match: last`** — if the `end` regex matches a per-page footer (a
   separator + page total that repeats), tell `parse_by_rule` to use the LAST
   occurrence so the block spans all pages.
2. **`skip_line`** — drop lines that would otherwise wrongly match the item
   regex (page headers, "Page X of Y", subtotal rows).

```yaml
lines:
  start: ^ITEMS$
  end: ^_+\n\s*Total this page
  end_match: last
  line: (?P<sku>\S+)\s+(?P<qty>\d+)
  skip_line:
    - ^Page \d+ of \d+
    - ^Acme Corp \| Invoice continued
```

## "Two templates both match the invoice"

Set `priority` on the more specific one so it wins:

```yaml
issuer: ACME (invoice)
priority: 10        # default is 5; higher = tried first
keywords:
  - ACME Ltd
  - Invoice
```

## "The captured value has garbage I want to strip"

Use `replace` on the field — one pair or a list of pairs, applied before type
coercion:

```yaml
vat:
  parser: regex
  regex: 'VAT\s+(\S+)'
  replace: ['\W+', '']     # NL.999,999.999,B01 -> NL999999999B01
```

## "Unit strings should map to UNECE codes"

invoice2data already maps common `uom` literals to UNECE Rec 20 codes on each
line (`kg → KGM`, `pcs → H87`, `l → LTR`) when the field is absent — see
{doc}`recommended-template-fields` for the full table. To add a literal, extend
`invoice2data.extract.unece_uom.UNECE_CODES`.

## "Templates live in a database, not on disk"

`ordered_load` parses a template list from a string; hand the result to
`extract_data(..., templates=...)`. Any downstream app (Odoo, a Django admin,
your own service) can hold templates in a table:

```python
from invoice2data import extract_data
from invoice2data.extract.loader import ordered_load

templates = ordered_load(db.query("SELECT body FROM invoice_templates").body)
result = extract_data("invoice.pdf", templates=templates)
```

For YAML instead of JSON: `ordered_load(text, loader=yaml.safe_load)`.

## "I want to catch parse failures precisely (not just an empty dict)"

Opt in to typed errors:

```python
from invoice2data import extract_data
from invoice2data.exceptions import (
    NoTemplateFoundError,
    RequiredFieldsMissingError,
)

try:
    result = extract_data("invoice.pdf", raise_on_error=True)
except RequiredFieldsMissingError as exc:
    print("Template matched but incomplete:", exc.fields)
except NoTemplateFoundError:
    print("No template at all — consider --ai-fallback or a new template")
```

Both inherit `InvoiceProcessingError`. The default (no `raise_on_error`) is
still `return {}` — this is opt-in.

## "One CSV row per line item, not one per invoice"

```bash
invoice2data --output-format csv --csv-lines=explode invoice.pdf
```

Default is `--csv-lines=json` (one row per invoice, `lines` cell is a JSON
blob). `explode` produces one row per line item with the invoice-level columns
duplicated.

## "Machine-readable logs for a CI / cron pipeline"

```bash
invoice2data --in-automation --output-format json --output-name - *.pdf 2>logs.jsonl | jq .
```

`--in-automation` swaps the log formatter for one-JSON-object-per-line on
stderr; `--output-name -` streams the extracted-fields JSON on stdout;
so `2>logs.jsonl` cleanly separates the two streams.

## "OCR a scanned invoice + save the cleaned PDF back"

```python
from invoice2data.input.ocrmypdf import pre_process_pdf, RECOMMENDED_SCAN_OPTIONS

cleaned_pdf_path = pre_process_pdf("scan.pdf", pre_conf=RECOMMENDED_SCAN_OPTIONS)
# ... store cleaned_pdf_path in your invoice attachment ...
```

`RECOMMENDED_SCAN_OPTIONS` turns on `deskew`, `clean`, `rotate_pages`, and
`optimize` — the typical "make this scan usable" preset. Any
[ocrmypdf option](https://ocrmypdf.readthedocs.io/) can be passed via
`pre_conf`.

## "I need per-page area extraction on a specific field"

Set an `area:` on the field with the coordinates + resolution:

```yaml
fields:
  invoice_number:
    parser: regex
    regex: '(\d{5,})'
    area:
      f: 1     # first page
      l: 1     # last page (same = single page)
      r: 300   # DPI the coords are measured in
      x: 400   # left
      y: 50    # top
      W: 200   # width
      H: 30    # height
```

Backends that support area: `pdftotext` (native, uses `-x/-y/-W/-H`) and
`pdfium` (in-process crop). For area-critical templates pin the backend with
`input_module: pdftotext` at the top level (bundled area templates already do
this).
