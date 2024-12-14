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
| name | char | The name of the product, can be used for product matching |
| barcode | char | The the barcode of the product or product package, used for product matching |
| code | char | The (internal) product code, used for product matching |
| qty | float | The amount of items/units |
| unece_code | char | The unece code of the products units of measure can be passed |
| uom | char | The name of the unit of measure, internally if will be mapped to the unece code. Example L will be mapped to unece_code LTR |
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
        line: (?P<description>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price_total>\d+\d+)
```

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
        line: (?P<description>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price_total>\d+\d+)
```
