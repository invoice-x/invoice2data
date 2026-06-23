# Recommended fields

While invoice2data doesn't enforce a strict template structure, we strongly recommend using the standard template fields outlined in this section.
This ensures consistency, minimizes repetitive work, and allows you to take full advantage of the templating system.

## Partner fields

The following fields are recommended to identify the partner (issuer) of the invoice.

| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| vat | char | The vat code is unique for each partner, it has the highest priority for matching the partner  |
| partner_name | char | self explaining |
| partner_street | char | self explaining |
| partner_street2 | char | self explaining |
| partner_street3 | char | self explaining |
| partner_city | char | self explaining |
| partner_zip | char | self explaining |
| country_code | char | use iso format `fr` or `nl` |
| state_code | char | use iso format `NY` (for New York) |
| partner_email | char | self explaining |
| partner_website | char | self explaining |
| telephone | char | can be used for matching the partner with the help of support modules  |
| mobile | char | can be used for matching the partner contact with the help of support modules  |
| partner_ref | char | reference name or number can be used for partner matching |
| siren | char | French business code, can be used for matching the partner |
| partner_coc | char | General business identiefier number, can be used for matching the partner |

**Example Usage**
```yaml
    fields:
    partner_name:
      parser: regex
      regex: Azure Interior
```

## Invoice Fields (on document level)
| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| currency | char | The currency of the invoice in iso format (EUR, USD) |
| currency_symbol | char | The currency symbol of the invoice (€, $) |
| bic | char | Bank Identifier Code |
| iban | char | International Bank Account Number |
| amount | float | The total amount of the invoice (including taxes) |
| amount_untaxed | float | The total amount of the invoice (excluding taxes) |
| amount_tax | float | The sum of the tax amount of the invoice |
| date | date | The date of the invoice |
| invoice_number | char | self explaining |
| date_due | date | The duedate of the invoice |
| date_start | date | The start date of the period for the invoice when the services are delivered. |
| date_end | date | The start date of the period for the invoice when the services are delivered. |
| note | char | The contents of this field will be imported in the chatter. |
| narration | char | The contents of this field will be imported in the narration field. (on the bottom of the invoice.) |
| payment_reference | char | If the invoice is pre-paid an reference can be used for payment reconciliation |
| payment_unece_code | char | The unece code of the payment means according to 4461 code list |
| incoterm | char | The Incoterm 2000 abbrevation |
| company_vat | char | The vat number of the company to which the invoice is addressed to. Used to check if the invoice is actually is adressed to the company which wants to process it. (Very useful in multi-company setup) |
| mandate_id | char | A banking mandate is attached to a bank account and represents an authorization that the bank account owner gives to a company for a specific operation (such as direct debit). |


## Invoice Line Fields

To be used in the lines section:


| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| name | char | The invoice line's label/description (Odoo line `name`). `description` is accepted as an alias and normalized to `name`. |
| product | char | Product identifier (name or code) used for product matching. Distinct from `name`. |
| taxes | char | Tax identifier(s) used for tax matching (the no-product line method). |
| barcode | char | The the barcode of the product or product package, used for product matching |
| code | char | The (internal) product code, used for product matching |
| qty | float | The amount of items/units |
| unece_code | char | The unece code (Recommendation 20) of the line's unit of measure. Auto-derived from `uom` when present — see *UoM normalization* below. |
| uom | char | The printed unit of measure exactly as it appears on the invoice; mapped to `unece_code` when the literal is known. |
| price_unit | float | The unit price of the item. (excluding taxes) |
| discount | float | The amount of discount for this line. Eg 20 for 20% discount or 0.0 for no discount |
| price_total | float | The total amount of the invoice line including taxes. It can be used to select the correct tax tag. |
| price_subtotal | float | The total amount of the invoice line excluding taxes. It can be used to create adjustment lines when the decimal precision is insufficient. |
| line_tax_percent | float | The percentage of tax |
| line_tax_amount | float | The fixed amount of tax applied to the line |
| line_note | char | Notes on the invoice can be imported, There is a special view available. |
| sectionheader | char | There is a special view available for section headers. |
| date_start | date | The start date of the period for the invoice when the services are delivered. |
| date_end | date | The start date of the period for the invoice when the services are delivered. |

**Example Usage**
```yaml
    lines:
        start: Item\s+Discount\s+Price$
        end: \s+Total
        line: (?P<name>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price_total>\d+\d+)
```

### Multi-page invoices (`end_match: last`)

When an invoice's items span multiple pages and the `end` regex matches a
*repeating* footer (totals/separator block on every page), set
`end_match: last` so the parser uses the **last** occurrence of `end` in the
`start`-bounded slice — letting the block span all pages. Combine with
`skip_line` to drop the per-page header/footer text between item rows.

```yaml
lines:
    start: ^ITEMS$
    end: ^_+\n\s*Total this page
    end_match: last     # span all pages; default is 'first'
    line: (?P<sku>\S+)\s+(?P<qty>\d+)\s+(?P<price>[\d.]+)
    skip_line:
      - ^Page \d+ of \d+
      - ^Acme Corp \| Invoice continued
```

For invoices where one line item's **description** spans multiple text lines
followed by the amounts on their own line, bracket each item with
`first_line` (description start) + `line` (continuation, repeats) + `last_line`
(the amounts row). The `line` matches accumulate into the same record (joined
with `\n`), and `last_line` closes it.

### Skipping unwanted lines (`skip_line`)

A `lines` block can drop lines that match an unwanted shape *before* its `line`
/ `first_line` / `last_line` matchers see them. Useful when a sub-total, tax,
or footer line would otherwise wrongly match the line regex.

```yaml
lines:
    line: (?P<name>.+)\s+(?P<qty>\d+)\s+(?P<price_total>\d+\.\d+)
    skip_line:
      - ^Subtotal
      - ^VAT
      - ^Total
```

A single pattern can be given as a string; multiple as a list.

### Extracting numbers from text (`extract_number`)

For regex fields whose capture contains units or currency mixed with the
number (e.g. `12123 Stk.`, `€25.50`, `4 Stück`), set `extract_number: true`
to pluck the first numeric token before type coercion. Sign, thousands and
decimal separators are preserved; parsing into `int`/`float` then proceeds
locale-aware via `parse_number`.

```yaml
fields:
  qty:
    parser: regex
    regex: 'Quantity\s+(\d+\s+Stk\.)'
    type: int
    extract_number: true
```

Opt-in per field — existing `int`/`float` fields keep their current behavior.

### UoM normalization (UNECE Rec 20)

invoice2data normalizes the printed unit of measure to its UNECE
Recommendation 20 code — the same code OCA's
`account_invoice_import_invoice2data` consumes — by mapping common literals on
each line:

| literal (case-insensitive)              | UNECE code |
| --------------------------------------- | ---------- |
| `l`, `ltr`, `liter`, `litre`, `ℓ`       | `LTR`      |
| `ml`                                    | `MLT`      |
| `kg`, `kilogram`                        | `KGM`      |
| `g`, `gr`, `gram`                       | `GRM`      |
| `m`, `meter`, `metre`                   | `MTR`      |
| `cm` / `mm` / `km`                      | `CMT` / `MMT` / `KMT` |
| `pcs`, `pc`, `piece`, `ea`, `unit`, `stuk`, `stk`, `x`, ...  | `H87` |
| `set`                                   | `SET`      |
| `h`, `hour`, `uur`                      | `HUR`      |
| `min`, `minute`                         | `MIN`      |
| `d`, `day`, `dag`                       | `DAY`      |
| `month`, `maand`, `mnd`                 | `MON`      |
| `year`, `jaar`                          | `ANN`      |

A template that already captures `unece_code` directly always wins; the
mapping only fills in `unece_code` when it's missing. Unknown literals are
left alone (their `uom` is preserved). To add literals, extend
`UNECE_CODES` in `invoice2data.extract.unece_uom`.

## Tax Line Fields

To be used in the Tax lines section of an invoice:

Example of an Tax line section on a invoice:

```
                                                EXCL. VAT             VAT-PERCENTAGE              VAT-AMOUNT
                                                      0.00                    0.0                     0.0
                                                      0.00                    9.0                     0.0
                                                     42.73                   21.0                     8.97
```


| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| price_subtotal | float | The total amount of the tax rule excluding taxes. |
| line_tax_percent | float | The percentage of tax. |
| line_tax_amount | float | The amount of tax for the tax line. |

**Example Usage**
```yaml
    lines:
        start: Item\s+Discount\s+Price$
        end: \s+Total
        line: (?P<name>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price_total>\d+\d+)
```
