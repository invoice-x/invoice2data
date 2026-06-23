# Migrating to invoice2data 1.0

1.0 is a major release that modernizes the toolchain and cleans up long-standing
legacy behaviour. This page tracks what changes, what is deprecated, and how to
migrate.

## Python support

- 1.0 requires **Python 3.10+** (3.8 and 3.9 were dropped in the 0.4.x line).
- Raising the floor to **3.11** is planned for a later release, not 1.0.

## Deprecations (still work in 1.0, removed in a future major)

Deprecated features emit a `DeprecationWarning`. Run Python with `-W default` (or
`pytest`) to see them.

### The `lines` *plugin* → the `lines` *parser*

Defining line items with a **top-level `lines:` key** uses the legacy `lines`
*plugin*. Define it instead as a **field** with `parser: lines` (identical
behaviour, one canonical syntax):

```yaml
# Deprecated (top-level key, the "lines" plugin):
lines:
  start: 'Item'
  end: 'Total'
  line: '(?P<description>.+)\s+(?P<price>\d+[.,]\d{2})'

# Preferred (a field using the "lines" parser):
fields:
  lines:
    parser: lines
    start: 'Item'
    end: 'Total'
    line: '(?P<description>.+)\s+(?P<price>\d+[.,]\d{2})'
```

## Retained in 1.0 (under review for a future major)

These remain fully supported in 1.0. They are documented here because they may
be revisited later — **feedback welcome** on the tracker before any change.

- **Field-name shorthand**: `field: 'regex'` as a terse alternative to
  `field: {parser: regex, regex: 'regex'}`.
- **Auto-typing by name**: a field whose name starts with `amount`/ends with or
  starts with `date` is coerced to float/date without an explicit `type:`.
- **`static_` prefix** (e.g. `static_vat: FR123…`) — a constant value. Equivalent
  to `parser: static`. Widely used (~half of the built-in templates), so retained.
- **`sum_amount…` prefix** with a list of regexes — sums the matches. Equivalent
  to `parser: regex` + `group: sum`.

## Clarified behaviour

- **`extract_data()` return value**: returns the extracted-fields `dict`, or an
  **empty dict `{}`** when text extraction fails or no template matches. (It does
  not return `False`; older docs said so.)

## Landed in 1.0

- **Field validation** (`extract/schema.py`): output field names are checked
  against the recommended vocabulary. It is quiet by default — a field is only
  flagged when it looks like a **typo** of a canonical name (custom fields are
  fine). Opt into strict checking per template with `options.strict_fields:
  true` (raises on any unrecognized field), and whitelist custom names with
  `options.extra_fields: [...]`.
- **Computed `tax_lines` amounts**: a missing `line_tax_amount` in a `tax_lines`
  row is computed from `price_subtotal * line_tax_percent / 100` (never
  overwrites existing values). An advisory warning is logged if `tax_lines`
  don't sum to `amount_tax`.
- **Typed extraction errors** (issue #190): `extract_data(..., raise_on_error=True)`
  raises an `InvoiceProcessingError` instead of returning `{}` —
  `RequiredFieldsMissingError` (with `.fields`) when a template matched but a
  required field couldn't be parsed, else `NoTemplateFoundError`. Opt-in and
  non-breaking; the default still returns `{}`. The errors subclass `ValueError`,
  so existing cascade handling is unaffected. Importable from `invoice2data`.
- **UoM → UNECE Rec 20 normalization** (issue #497 follow-up): each line's
  printed `uom` literal is mapped to a canonical UNECE Recommendation 20 code
  on `unece_code` when the latter is missing (e.g. `kg → KGM`, `pcs → H87`,
  `l → LTR`). Auto-populates only — an explicit `unece_code` always wins and
  unknown literals are left alone. Lookup lives in `extract.unece_uom`. See
  *UoM normalization* in `docs/recommended-template-fields.md` for the full
  table. **Additive but visible**: output dicts now carry the extra key
  for any line that previously had a known `uom` literal without an
  `unece_code`.
- **Tax rate applied to invoice lines** (issue #535): when product `lines` carry
  a `line_tax_code` and the `tax_lines` summary maps that code to a
  `line_tax_percent`, the rate is copied onto each matching line (and its
  `line_tax_amount` computed). Existing line values are never overwritten. When
  lines carry no code but the summary has a single active (non-zero) rate, that
  rate is applied to every line; mixed-rate summaries are left untouched.
- **CSV output** now JSON-encodes `lines`/`tax_lines` cells (valid, parseable
  CSV) instead of writing Python `repr`. **Breaking** for anything that parsed
  the previous output. New `--csv-lines={json,explode}` (`explode` writes one
  row per line item).
- **Faster regex**: patterns are compiled once and cached. The API-compatible
  `regex` engine can be opted into with `INVOICE2DATA_REGEX_ENGINE=regex`; the
  default remains stdlib `re` (non-breaking).
- **Pluggable input backends**: a documented backend interface and registry
  (`input/__interface__.py`); `extract_data` still accepts module or string.
- **Input-backend cascade + per-template backend**: when no backend is forced,
  `extract_data` tries an ordered cascade (`DEFAULT_INPUT_READERS`) until a
  template matches with all required fields, then OCR (ocrmypdf) as a last
  resort. A template can pin the backend it was authored for with a top-level
  `input_module:` key (e.g. `input_module: pdftotext` for a layout-sensitive
  template); that backend is then used for it in auto mode. Forcing
  `--input-reader`/`input_module=` keeps the old single-pass behaviour (and now
  takes the backend at face value — it ignores a template's pin). A
  matched-but-incomplete extraction returns `{}` (per the documented contract)
  instead of raising `ValueError`.
- **Default backend is now pypdfium2** (`DEFAULT_INPUT_READERS = [pdfium,
  pdftotext]`). It is fast and dependency-light; `pdftotext` (poppler
  `-layout`) is the fallback. The cascade keeps accuracy at the pdftotext level
  (see [backend benchmark](backend-benchmark.md)) because it falls back
  automatically when pypdfium2 fails to match, misses a required field, or
  drops a declared line-item table (empty `lines`/`tables`). **Migration for
  template authors:** a template whose *non-required* field is silently wrong
  under pypdfium2 — typically an `area:` field or a column-aligned table that
  comes back populated but incorrect — should pin `input_module: pdftotext`.
  The bundled layout/area templates that need it are already pinned.
- **Camelot table plugin** (opt-in): a new `camelot` plugin extracts ruled or
  whitespace-aligned tables by re-reading the PDF with
  [camelot-py](https://pypi.org/project/camelot-py/). Install the extra
  (`pip install invoice2data[camelot]`) and add a top-level `camelot:` block to
  a template (forwarding `camelot.read_pdf` options like `flavor`/`pages`, plus
  `field`/`header`/`tables`). It self-excludes when camelot is not installed.
  **Note:** the published camelot-py pins a newer `pdfminer.six` than
  `pdfplumber`, so the `camelot` extra is mutually exclusive with the
  `pdfplumber` and `pdfminer-six` extras (run camelot alongside the default
  pdfium/pdftotext cascade). Plugins now also receive the source `invoice_file`.
- **Canonical `lines`/`tax_lines` field names**: line-item output keys are
  normalized to one vocabulary at extraction time
  (`schema.normalize_line_fields`), so templates may keep their own group names
  and still emit standard fields: `description → name`, `unit_price`/`unitprice
  → price_unit`, `vat_rate`/`tax_percent → line_tax_percent`. The canonical
  vocabulary now also documents the distinct **`product`** (product matching —
  *not* a synonym for `name`) and **`taxes`** (tax matching) line fields.
  **Breaking** for downstream code that read the old key names. The bundled
  templates were also tidied to use the canonical names directly.
- **Per-field `replace`** (issue #497): a `regex`-parser field can sanitize its
  captured value with `replace: [pattern, repl]` (or a list of pairs), applied
  *before* type coercion. Lines/tables blocks accept the same convention as a
  `{sub-field: [pattern, repl]}` map. Useful for stripping currency symbols /
  whitespace / unwanted glyphs while keeping the regex itself simple.
- **`extract_number: true` per-field option** (issue #652): plucks the first
  numeric token out of a captured value that contains text or units mixed
  with the number (e.g. `12123 Stk.` → `12123`, `€25.50` → `25.50`). Opt-in;
  existing `int`/`float` fields unaffected.
- **`skip_line:` for lines blocks** (issue #652): drops lines matching a
  pattern (or list of patterns) before the `line` / `first_line` / `last_line`
  matchers see them. Catches sub-total / VAT / page-footer rows that would
  otherwise wrongly match the line regex.
- **Multi-page lines: `end_match: last`** (issue #650): tells `parse_by_rule`
  to use the LAST occurrence of `end` in the `start`-bounded slice, so a
  block can span all pages when the `end` pattern matches a per-page footer.
  Combine with `skip_line` to drop repeating headers between item rows.
- **Tiered date parsing** (`extract/_dates.py`): `parse_date` tries
  `strptime` against the template's `date_formats` first, then `dateutil`,
  then the optional `dateparser`. `dateparser` is now an **optional** extra
  (`pip install invoice2data[dateparser]`) — needed only for localized
  month-name dates. Templates that set `date_formats` get the strptime
  fast-path; 186 of 215 bundled templates do as of 1.0.
- **Label-driven field detection** (`extract/labels.py`): a separate
  `find_labeled_fields(text)` helper recognises `label [sep] value` pairs
  with multilingual synonyms (BTW/VAT, KvK/CoC/Chamber of Commerce, Invoice
  No/Factuurnummer/Rechnungsnummer, IBAN, BIC, Due Date/Vervaldatum, ...).
  Powers the template builder; not invoked at extraction time.
- **Typed candidate extraction + value validators**
  (`extract/candidates.py`, `extract/validators.py`): typed extraction of
  date/amount/IBAN/VAT/BIC candidates from raw text, with offline
  validators (IBAN mod-97 / VAT format / BIC format) to disambiguate
  overlapping patterns. Powers the template builder.
- **Copier-style template builder** (`--new-template <sample.pdf>`): walks
  the user through a draft template using the candidate/label/validator
  machinery above. With `--ai`, uses an `AIProvider` to draft the YAML
  instead; with `--interactive`, prompts keep/edit/skip per field. Generated
  templates use the canonical schema.
- **AI extraction (opt-in, runtime + authoring time)**: pluggable
  `AIProvider` interface with a `MockProvider` (tests) and an
  `OpenAICompatibleProvider` (Gemini/Mistral/DeepSeek/Ollama via their
  OpenAI-compatible endpoints). `extract_data(..., ai_fallback=True)` triggers
  the LLM when no template matches; `--new-template --ai` drafts a template
  from a sample. Output flows through the canonical `validate_output`
  layer; results are tagged with `extraction_method: "ai"`. Provider-pluggable,
  key-gated, never the default.
- **Camelot table plugin gains an `excalibur_to_template` helper**
  (`extract/excalibur.py`): converts an Excalibur rule JSON export into a
  ready-to-paste `camelot:` template stanza. A Jupyter notebook with
  `camelot.plot(...)` is a viable alternative authoring path since the
  converter accepts any dict in the same shape.
- **OCR backends**: the existing `gvision` (Google Cloud Vision) backend
  modernized for the current Cloud Vision API; new **DocTR** and
  **PaddleOCR** backends added for fully-local deep-learning OCR
  (`pip install invoice2data[doctr]` / `[paddleocr]`). `ocrmypdf` knobs
  (deskew, clean, rotate, oversample) documented; the preprocessed PDF
  returned alongside the text so downstream tooling can re-attach the
  cleaned scan.
- **mypyc-compiled hot paths** (opt-in at build time via
  `INVOICE2DATA_COMPILE_MYPYC=1`): the 5 leaf hot modules (`extract/utils`,
  `_regex`, `parsers/regex`, `parsers/lines`, `plugins/tables`) compile to
  native code; the published wheels ship the compiled binaries via
  cibuildwheel for Linux/macOS/Windows × Python 3.10–3.13. The sdist stays
  pure-Python.
- **CLI quality-of-life (issue #608)**: `--no-color` (also honours `NO_COLOR`),
  `--debug-optimized-str`, `--in-automation` (one-JSON-per-line logging),
  `--output-name -` / `/dev/stdout` / `/dev/stderr`, and
  `template_name` in default output (issue #618).
- **Streaming/DB-stored templates**:
  `ordered_load(stream, loader=json.loads)` parses templates from a string
  (JSON by default, YAML when `loader=yaml.safe_load`), so a downstream app
  can serve templates from a database or API and pass them via
  `extract_data(file, templates=ordered_load(blob))`.

## Feedback

Please raise questions or objections to any deprecation on the
[issue tracker](https://github.com/invoice-x/invoice2data/issues) before 1.0 is
cut, especially if a deprecated feature is important to your templates.
