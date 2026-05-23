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

## Planned for 1.0 (tracked, not yet landed)

- **Field/output validation**: output field names/types validated against the
  recommended vocabulary; unknown/legacy names warn (a `--strict` mode will be
  available to turn warnings into errors). Non-strict by default.
- **Canonical `tax_lines`/`lines` schema** and **CSV output that flattens line
  arrays**. The CSV change is **breaking** for anything parsing the previous
  (broken) CSV, which serialized line arrays as Python `repr` strings.
- **Faster regex** (already landed): patterns are compiled once and cached. The
  API-compatible `regex` engine can be opted into with
  `INVOICE2DATA_REGEX_ENGINE=regex`; the default remains stdlib `re` (non-breaking).
- **Pluggable input backends** (already landed) plus new fast PDF backends
  (pypdfium2 and others), selectable via `--input-reader` (additive, non-breaking).

## Feedback

Please raise questions or objections to any deprecation on the
[issue tracker](https://github.com/invoice-x/invoice2data/issues) before 1.0 is
cut, especially if a deprecated feature is important to your templates.
