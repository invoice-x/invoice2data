# Tutorial for Template Creation

A template defines the data you want to extract from an invoice. Each template should work for all invoices from the same company or subsidiary (e.g., Amazon Germany vs. Amazon US).

Creating templates is easy and shouldn't take longer than manually entering 2-3 invoices. We use a simple YAML or JSON format. Many fields are optional and are only needed for edge cases.

## Finding Existing Templates

Existing templates are located in the ["templates"](https://github.com/invoice-x/invoice2data/tree/master/src/invoice2data/extract/templates) folder of the installed package. You can use the `--template-folder` option to specify your own template files.

**Contributing:** If you create or improve templates that could benefit others, please submit a pull request to the main repository.

## Simple Invoice Template

Here's a minimal template example for Microsoft Hong Kong invoices:

```yaml
issuer: Microsoft Regional Sales Corporation
keywords:
  - Microsoft
  - M9-0002526-N
exclude_keywords:
  - Already\s+paid
  - Do not pay
fields:
  amount: GrandTotal(\d+\.\d+)HKD
  date: DocumentDate:(\d{1,2}\/\d{1,2}\/\d{4})
  invoice_number: InvoiceNo.:(\w+)
options:
  remove_whitespace: true
  currency: HKD
  date_formats:
    - '%d/%m/%Y'
```

*Explanation:*

- `issuer`: The name of the invoice issuer. Can have the company name and country.
- `keywords`: Required. These are unique words used to pick the
  correct template. Be as specific as possible. As we add more
  templates, we need to avoid duplicate matches. Using the VAT number,
  email, website, phone, etc are generally good choices. ALL keywords
  need to match to use the template.
  These keywords are regex patterns, so 'Company US' and 'Company\s+US' both work.
  This also allows some flexibility as 'Company\s+(US|UK)' will match on both
  Company US and Company UK.
- `exclude_keywords`: Optional. Regex patterns that, if matched, prevent the template from being used.

## Fields & Parsers

This section defines the data to extract and how.

Each field can be:

- An **associative array** with
  `parser` (required) specifying parsing method and
  `area` (optional) specifying the region of the pdf to search.
  This takes the following arguments: `f` (first page), `l` (last page), `x` (top-left x-coord), `y` (top-left y-coord),
  `r` (resolution), `W` (width in pixels) and `H` (height in pixels). When setting your region, ensure the resolution in your
  image editor matches the resolution specified for `r` in this option. If not, it will not line up properly.
- A single regex with one capturing group
- An array of regexes

**Required Fields:** Every template must have at least `amount`, `date`, and `invoice_number`.

**Standard fields:**

- `date`: Invoice issue date.
- `invoice_number`: Unique number assigned to invoice by an issuer.
- `amount`: Total amount (with taxes).
- `vat`: [VAT identification number](https://en.wikipedia.org/wiki/VAT_identification_number)
- `tax_lines`: [structure](#Tax-lines) containing detailed tax information


## Template Structure
````{important}
While invoice2data doesn't enforce a strict template structure, we strongly recommend using the standard template fields outlined in this documentation. This ensures consistency, minimizes repetitive work, and allows you to take full advantage of the templating system.

Although invoice2data is designed for extracting data from invoices, many users find it helpful for other document types as well. Feel free to adapt the template structure to suit your specific needs.

However, for optimal results and compatibility with future updates, adhering to the [recommended template fields](#recommended-template-fields) is advised.
````

### Parser `regex`

This is the basic parser for extracting data using regular expressions. The only required property is `regex`, which can contain a single regex pattern or an array of multiple patterns.

You don't need to include the entire regex in the capturing group. Often, you'll use keywords and only capture the relevant part of the match (e.g., the amount).

**Understanding Regular Expressions**

You'll need to understand regular expressions to effectively use this parser. If you're new to regex, here are some resources:

* [Regex Tutorial](http://www.zytrax.com/tech/web/regex.htm)
* [Regex Tester](http://www.regexr.com/)

We use [Python's regex engine](https://docs.python.org/2/library/re.html). While this usually won't matter for simple expressions, be aware of potential subtle differences if you're used to other regex flavors (like Perl).

**Duplicate Matches**

By default, the `regex` parser removes duplicate matches. This means you'll get a single value or an array of unique values.

**Optional Properties**

* **`type`**:  Specifies the data type of the extracted value. Can be `int`, `float`, or `date`.
* **`group`**: Defines how to handle multiple matches. Options include:
    * `sum`: Sum the values.
    * `min`: Return the minimum value.
    * `max`: Return the maximum value.
    * `first`: Return the first match.
    * `last`: Return the last match.
    * `join`: Join the matches into a single string.

**Example**

```yaml
fields:
  amount:
    parser: regex
    regex: Total:\s+(\d+\.\d+) EUR
    type: float
  date:
    parser: regex
    area: {f: 1, l: 1, x: 110, y: 50, r: 300, W: 100, H: 200}
    regex: Issued on:\s+(\d{4}-\d{2}-\d{2})
    type: date
  advance:
    parser: regex
    regex:
      - Advance payment:\s+(\d+\.\d+)
      - Paid in advance:\s+(\d+\.\d+)
    type: float
    group: sum
```

### Parser `static`

This parser allows you to set a field to a fixed value. This is useful for fields that always have the same value on a particular type of invoice.

**Properties**

* **`value`:** The fixed value to assign to the field.

**Example**

```yaml
fields:
  friendly_name:
    parser: static
    value: Amazon
```

### Parser `lines`

This parser allows parsing selected invoice section as a set of lines
sharing some pattern. Those can be e.g. invoice items (good or services)
or VAT rates.

Some companies may use multiple formats for their line-based data. In
such cases multiple sets of parsing regexes can be added to the `rules`.
Results from multiple `rules` get merged into a single array.

**Properties**

* **`start`:** A regex to identify the beginning of the line item section.
* **`end`:** A regex to identify the end of the line item section.
* **`line`:** A regex with named capture groups to extract data from each line. The names of the capture groups become the field names in the output.
* **`rules` (optional):**  Allows you to define multiple sets of `start`, `end`, and `line` regexes. This is helpful when a company uses different formats for their line items. Results from all rules are merged into a single array.

**Replacing the `lines` Plugin**

This parser replaces the older `lines` plugin and is the preferred method for extracting line item data. It's more flexible and can be reused across multiple fields.

**Example**

Example for `fields`:
```yaml
    fields:
      lines:
        parser: lines
        start: Item\s+Discount\s+Price$
        end: \s+Total
        line: (?P<description>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price_total>\d+\d+)

    fields:
      lines:
        parser: lines
        rules:
          - start: Item\s+Discount\s+Price$
            end: \s+Total
            line: (?P<description>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price_total>\d+\d+)
          - start: Item\s+Price$
            end: \s+Total
            line: (?P<description>.+)\s+(?P<price_total>\d+\d+)
```

### Legacy Regexes

This section describes older conventions for defining fields using regexes. While these methods still work, using the `regex` parser with explicit `type` and `group` properties is generally preferred for clarity and flexibility.

**Field Name Conventions**

* **`date_` prefix:** Fields with names starting with `date_` are automatically treated as date fields.
* **`amount_` prefix:** Fields with names starting with `amount_` are automatically treated as float fields.

**Special Prefixes**

* **`static_`:**  This prefix defines a static field. The field will be set to the value specified in the regex, and no regular expression matching will be performed.
* **`sum_`:** This prefix, when used with a list of regexes, will sum the values captured by each regex.

**Note:** These special prefixes are removed from the field names in the output.

**Example with `sum_`**

```yaml
fields:
  sum_amount_tax:
    - VAT\s+10%\s+(\d+,\d{2})
    - VAT\s+20%\s+(\d+,\d{2})
```
If the first regexp for `VAT 10%` catches **1.5** and the second regexp for
`VAT 20%` catches **4.0**, the output will be
````
{'amount_tax': 5.50, 'date':...}
````
As you can see, the sum_ prefix is removed from the amount_tax field name.


### Lines

The `lines` key allows you to extract line item data from invoices, such as product descriptions, quantities, and prices.

**Required Properties**

* **`start`**: A regex to identify the beginning of the line item section.
* **`end`**: A regex to identify the end of the line item section.
* **`line`**: A regex with named capture groups to extract data from each line. The names of the capture groups will become the field names in the output.

**Optional Properties**

* **`skip_line`**: A regex pattern which indicates sub-lines will be skipped and their data not recorded. This is useful if tables span multiple pages and you need to skip over page numbers or headers that appear mid-table.

**Example Invoice**

If we have an invoice that looks like
```
    some header text

    the address, etc.

      Item        Discount      Price

     1st item     0.0 %           42.00
     2nd item     10.0 %          37.80

                          Total   79.80

    A footer
```

**Example Template**
```yaml
    lines:
        start: Item\s+Discount\s+Price$
        end: \s+Total
        line: (?P<description>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price_total>\d+\d+)
```

**Data Types**

By default, all extracted fields are treated as strings. You can use the types key to specify the data type for each field:


```yaml
    types:
        discount: float
        price_total: float
```

#### Handling Multiple Lines per Item

Some invoices may have multiple lines per item. To handle this, you can use the `first_line` and/or `last_line` regexes:

* **`first_line`**: A regex to identify the first line of an item.
* **`last_line`**: A regex to identify the last line of an item.

The parser will check each line against these regexes in the following order:

1. `first_line` (if defined)
2. `last_line` (if defined)
3. `line`

If a line matches `first_line`, it starts a new item. If it matches `last_line`, it ends the current item. If it matches `line`, it's considered part of the current item. If none of the regexes match, the line is ignored.

````{important}
When using `first_line` and `last_line`, make sure that `first_line` is the most specific regex and `line` is the least specific.
````

### Tables Plugin

The `tables` plugin allows you to extract data from tables where the column headers and their corresponding values are on different lines. This is often the case in invoices where data is presented in a more visual, tabular format.

**How it Works**

The plugin uses the following properties:

* **`start`**: A regex to identify the beginning of the table.
* **`end`**: A regex to identify the end of the table.
* **`body`**: A regex with named capture groups to extract the data. The names of the capture groups will become the field names in the output.

**Optional Properties**

* **`type`**:  Specifies the data type of the extracted value. Can be `int`, `float`, or `date`.
* **`group`**: Defines how to handle multiple matches. Options include:
    * `sum`: Sum the values.
    * `min`: Return the minimum value.
    * `max`: Return the maximum value.
    * `first`: Return the first match.
    * `last`: Return the last match.
    * `join`: Join the matches into a single string.

The plugin will try to match the `body` regex to the text between the `start` and `end` markers.

**Example Invoice**

Here's an example of an invoice with table-like data:

    Guest Name: Sanjay                                                                      Date: 31/12/2017

    Hotel Details                                                   Check In            Check Out       Rooms
    OYO 4189 Resort Nanganallur,                                    31/12/2017          01/01/2018      1
    25,Vembuliamman Koil Street,, Pazhavanthangal, Chennai
                                                                        Booking ID              Payment Mode
                                                                        IBZY2087                Cash at Hotel

    DESCRIPTION                                             RATE                                    AMOUNT

    Room Charges                                            Rs 1939 x 1 Night x 1 Room              Rs 1939

    Grand Total                                                                                     Rs 1939

    Payment received by OYO                                 Paid through Cash At Hotel (Rs 1939)    Rs 1939

    Balance ( if any )                                                                              Rs 0

The hotel name, check in and check out dates, room count, booking ID,
and payment mode are all located on different lines from their column
headings. A template to capture these fields may look like:
```yaml
    tables:
      - start: Hotel Details\s+Check In\s+Check Out\s+Rooms
        end: Booking ID
        body: (?P<hotel_details>[\S ]+),\s+(?P<date_check_in>\d{1,2}\/\d{1,2}\/\d{4})\s+(?P<date_check_out>\d{1,2}\/\d{1,2}\/\d{4})\s+(?P<qty_rooms>\d+)
        types:
          qty_rooms: int
      - start: Booking ID\s+Payment Mode
        end: DESCRIPTION
        body: (?P<booking_id>\w+)\s+(?P<payment_method>(?:\w+ ?)*)
```
The plugin supports multiple tables per invoice as seen in the example.

By default, all fields are parsed as strings. The `tables` plugin
supports the `amount` and `date` field naming conventions to convert
data types.

The table plugin supports the grouping options in case there are multiple matches.
This is usefull when one wants to sum the numbers in a column, Example:
```yaml
    tables:
      - start: Basic example to sum a number
        end: with the help of the table plugin
        body: (?P<random_num_to_sum>\d+\.\d+)
        fields:
          random_num_to_sum:
            group: sum
            type: float
```

### Options

Everything under `options` is optional. We expect to add more options in
the future to handle edge cases we find. Currently the most important
options and their defaults are:

- `currency` (default = `EUR`): The currency code returned. Many
  people will want to change this.
- `decimal_separator` (default = `.`): German invoices use `,` as
  decimal separator. So here is your chance to change it.
- `remove_whitespace` (default = `False`): Ignore any spaces. Often
  makes regex easier to write. Also used quite often.
- `remove_accents` (default = `False`): Useful when in France. Saves
  you from putting accents in your regular expressions.
- `lowercase` (default = `False`): Similar to whitespace removal.
- `date_formats` (default = `[]`): We use dateparser/dateutil to
  'guess' the correct date format. Sometimes this doesn't work and you
  can set one or more additional date formats. These are passed
  directly to [dateparser](https://github.com/scrapinghub/dateparser).
- `languages` (default = \[\]): Also passed to `dateparser` to parse
  names of months.
- `replace` (default = `[]`): Additional search and replace before
  matching. Each replace entry must be a list of two elements.
  The first is the regex pattern to be replaced, the second the string
  to replace any matches with. Replacing is not typically needed.
- `required_fields`: By default the template should have regex for
  date, amount, invoice_number and issuer. If you wish to extract
  different fields, you can supply a list here. The extraction will
  fail if not all fields are matched.

### Priority

In case of multiple templates matching single invoice the one with the
highest priority will be used. Default `priority` value (assigned if
missing) is 5.

This property needs to be specified only when designing some generic or
very specific templates.

Suggested values:

- 0-4: accounting/invoice software specific template
- 5: company specific template
- 6-10: company department/unit specific template

(Tax-lines)=
### Tax-lines

Invoices / receipts often have a table near the bottom with a summary of the appied VAT taxes.
To correctly process the invoice in accounting programs we need separatly parse the amount per tax type.

Example invoice:

```
                                                EXCL. VAT             VAT-PERCENTAGE              VAT-AMOUNT
                                                      0.00                    0.0                     0.0
                                                      0.00                    9.0                     0.0
                                                     42.73                   21.0                     8.97
```


| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| price_subtotal | float | The total amount of the tax rule excluding taxes. |
| line_tax_percent | float | The percentage of tax |
| line_tax_amount | float | The amount of tax for the tax line |

Example template:

```yaml
  tax_lines:
    parser: lines
    start: 'EXCL. VAT'
    end: '\Z'
    line:
      - '(?P<price_subtotal>[\d+.]+)\s+(?P<line_tax_percent>[\d+.]+)\s+(?P<line_tax_amount>[\d+.]+)'
    types:
      price_subtotal: float
      line_tax_percent: float
      line_tax_amount: float
```

## Example of template using most options
```yaml
    issuer: Free Mobile
    fields:
      amount: \spayer TTC\*\s+(\d+.\d{2})
      amount_untaxed: Total de la facture HT\s+(\d+.\d{2})
      date: Facture no \d+ du (\d+ .+ \d{4})
      invoice_number: Facture no (\d+)
      static_vat: FR25499247138
    keywords:
      - FR25499247138
      - Facture
    required_fields:
      - vat
      - invoice_number
    options:
      currency: EUR
      date_formats:
        - '%d %B %Y'
      languages:
        - fr
      decimal_separator: '.'
      replace:
        - ['e´ ', 'é']
        - ['\s{5,}', ' ']
```

## Steps to add new template

To add a new template, we recommend this workflow:

### 1. Copy existing template to new file

Find a template that is roughly similar to what you need and copy it to
a new file. It's good practice to use reverse domain notation. E.g.
`country.company.division.language.yml` or
`fr.mobile.enterprise.french.yml`. Language is not always needed.
Template folder are searched recursively for files ending in `.yml`.

### 2. Change invoice issuer

Just used in the output. Best to use the company name.

### 3. Set keyword

Look at the invoice and find the best identifying string. Tax number +
company name are good options. Remember, _all_ keywords need to be found
for the template to be used.

Keywords are compared _before_ processing the extracted text.

### 4. First test run

Now we're ready to see how far we are off. Run `invoice2data` with the
following debug command to see if your keywords match and how much work
is needed for dates, etc.

`invoice2data --template-folder tpl --debug invoice-XXX.pdf`

This test run shows you how the program will "see" the text in the
invoice. Parsing PDFs is sometimes a bit unpredictable. Also make sure
your template is used. You should already receive some data from static
fields or currencies.

### 5. Add regular expressions

Now you can use the debugging text to add regex fields for the
information you need. It's a good idea to copy parts of the text
directly from the debug output and then replace the dynamic parts with
regex. Keep in mind that some characters need escaping. To test, re-run
the above command.

- `date` field: First capture the date. Then see if `dateparser`
  handles it correctly. If not, add your format or language under
  options.
- `amount`: Capture the number _without_ currency code. If you expect
  high amounts, replace the thousand separator. Currently we don't
  parse numbers via locals (TODO)

### 6. Done

Now you're ready to commit and push your template, so others get a
chance to use and improve it.
