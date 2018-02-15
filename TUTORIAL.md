# Tutorial for template creation

A template defines which data attributes you wish to retrieve from an invoice. Each template should work on all invoices of a company or subsidiary (e.g. Amazon Germany vs Amazon US).

Adding templates is easy and shouldn't take longer than adding 2-3 invoices by hand. We use a simple YML-format. Many options are optional and you just need them to take care of edge cases.

Existing templates can be found in the project folder or the installed package under `/invoice2data/templates/`. During testing you can use the `--template-folder` option to point to your own, new template files. If you add or improve templates that could be useful for everyone, we encourage you to file a pull request to the main repo, so everyone can use it.

## Simple invoice template

Here is a sample of a minimal invoice template to read invoiced issued by Microsoft Hong Kong:

```
issuer: Microsoft Regional Sales Corporation
keywords:
- Microsoft
- M9-0002526-N
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

Let's look at each field:

- `issuer`: The name of the invoice issuer. Can have the company name and country.
- `keywords`: Also a required field. These are used to pick the correct template. Be as specific as possible. As we add more templates, we need to avoid duplicate matches. Using the VAT number, email, website, phone, etc are generally good choices. ALL keywords need to match to use the template.

### Fields
All the regex `fields` you need extracted. Required fields are `amount`, `date`, `invoice_number`. It's up to you, if you need more fields extracted. Each field has one or more regex with one regex capturing group. It's not required to put add the whole regex to the capturing group. Often we use keywords and only capture part of the match (e.g. the amount).

You will need to understand regular expressions to find the right values. If you didn't need them in your life up until now (lucky you), you can learn about them [here](http://www.zytrax.com/tech/web/regex.htm) or [test them here](http://www.regexr.com/). We use [Python's regex engine](https://docs.python.org/2/library/re.html). It won't matter for the simple expressions we need, but sometimes there are subtle differences when e.g. coming from Perl.

### Lines
The `lines` key allows you to parse invoice items. Mandatory are regexes `start` and `end` to figure out where in the stream the item table is located. Then the regex `line` is applied, and supposed to contain named capture groups. The names of the capture groups will be the field names for the parsed item. If we have an invoice that looks like

```
some header text

the address, etc.

  Item        Discount      Price

 1st item     0.0 %           42.00
 2nd item     10.0 %          37.80

                      Total   79.80

A footer
```

your lines definition should look like

```
lines:
    start: Item\s+Discount\s+Price$
    end: \s+Total
    line: (?P<description>.+)\s+(?P<discount>\d+.\d+)\s+(?P<price>\d+\d+)
```

Then if you want the parser to coerce the fields to numeric types (by default, they are strings), you can add a `types` key below `lines`:

```
    types:
        discount: float
        price: float
```

The example above is very simplistic, most invoices at least potentially can have multiple lines per invoice item. In order to parse this correctly, you can also give a `first_line` and/or `last_line` regex. For every line, the parser will check if `first_line` matches, if yes, it's a new line. If not, it checks if `last_line` matches, if yes, the current line is commited, if not, `line` regex is checked, and if this one doesn't match either, this line is ignored. This implies that you need to take care that the `first_line` regex is the most specific one, and `line` the least specific.

### Options

Everything under `options` is optional. We expect to add more options in the future to handle edge cases we find. Currently the most important options and their defaults are:

- `currency` (default = `EUR`): The currency code returned. Many people will want to change this.
- `decimal_separator` (default = `.`): German invoices use `,` as decimal separator. So here is your chance to change it.
- `remove_whitespace` (default = `False`): Ignore any spaces. Often makes regex easier to write. Also used quite often.
- `remove_accents` (default = `False`): Useful when in France. Saves you from putting accents in your regular expressions.
- `lowercase` (default = `False`): Similar to whitespace removal.
- `date_formats` (default = `[]`): We use dateparser/dateutil to 'guess' the correct date format. Sometimes this doesn't work and you can set one or more additional date formats. These are passed directly to [dateparser](https://github.com/scrapinghub/dateparser).
- `languages` (default = []): Also passed to `dateparser` to parse names of months.
- `replace` (default = `[]`): Additional search and replace before matching. Not needed usually.

### Example of template using most options

```
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
options:
  currency: EUR
  date_formats:
    - '%d %B %Y'
  languages:
    - fr
  decimal_separator: '.'
  replace:
    - ['e´ ', 'é']
```

## Steps to add new template

To add a new template, we recommend this workflow:

###1. Copy existing template to new file

Find a template that is roughly similar to what you need and copy it to a new file. It's good practice to use reverse domain notation. E.g. `country.company.division.language.yml` or `fr.mobile.enterprise.french.yml`. Language is not always needed. Template folder are searched recursively for files ending in `.yml`.

### 2. Change invoice issuer
Just used in the output. Best to use the company name.

### 3. Set keyword
Look at the invoice and find the best identifying string. Tax number + company name are good options. Remember, *all* keywords need to be found for the template to be used.

Keywords are compared *after* processing the extracted text. So if you use lowercase or remove-whitespace processing, adapt keywords accordingly.

### 4. First test run
Now we're ready to see how far we are off. Run `invoice2data` with the following debug command to see if your keywords match and how much work is needed for dates, etc.

`invoice2data --template-folder tpl --debug invoice-XXX.pdf`

This test run shows you how the program will "see" the text in the invoice. Parsing PDFs is sometimes a bit unpredictable. Also make sure your template is used. You should already receive some data from static fields or currencies.

### 5. Add regular expressions
Now you can use the debugging text to add regex fields for the information you need. It's a good idea to copy parts of the text directly from the debug output and then replace the dynamic parts with regex. Keep in mind that some characters need escaping.  To test, re-run the above command.

- `date` field: First capture the date. Then see if `dateparser` handles it correctly. If not, add your format or language under options.
- `amount`: Capture the number *without* currency code. If you expect high amounts, replace the thousand separator. Currently we don't parse numbers via locals (TODO)

### 6. Done
Now you're ready to commit and push your template, so others get a chance to use and improve it.
