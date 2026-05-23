# Migrating to invoice2data 1.0

1.0 is a major release that modernizes the toolchain and cleans up long-standing
legacy behaviour. This page tracks what changes, what is deprecated, and how to
migrate. It is updated as 1.0 work lands; nothing here is final until 1.0 ships.

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

## Planned for 1.0 (tracked, not yet landed)

- **Canonical `tax_lines`/`lines` schema**: normalize field names across the
  built-in templates to one vocabulary.
- **Camelot** table extraction and **mypyc**-compiled hot paths.

## Feedback

Please raise questions or objections to any deprecation on the
[issue tracker](https://github.com/invoice-x/invoice2data/issues) before 1.0 is
cut, especially if a deprecated feature is important to your templates.
