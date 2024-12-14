
How It Works
============

This part of the documentation includes a high-level explanation of how invoice2data extracts text from PDF files.

```mermaid

flowchart LR

    InvoiceFile[fa:fa-file-invoice Invoicefile\n\npdf\nimage\ntext] --> Input-module(Input Module\n\npdftotext\ntext\npdfminer\npdfplumber\ntesseract\ngvision)

    Input-module --> |Extracted Text| C{keyword\nmatching}

    Invoice-Templates[(fa:fa-file-lines Invoice Templates)] --> C{keyword\nmatching}

    C --> |Extracted Text + fa:fa-file-circle-check Template| E(Template Processing\n apply options from template\nremove accents, replaces etc...)

    E --> |Optimized String|Plugins&Parsers(Call plugins + parsers)

    subgraph Plugins&Parsers

      direction BT

        tables[fa:fa-table tables] ~~~ lines[fa:fa-grip-lines lines]

        lines ~~~ regex[fa:fa-code regex]

        regex ~~~ static[fa:fa-check static]



    end

    Plugins&Parsers --> |output| result[result\nfa:fa-file-csv,\njson,\nXML]



 click Invoice-Templates https://github.com/invoice-x/invoice2data/blob/master/docs/tutorial.md

 click result https://github.com/invoice-x/invoice2data#usage

 click Input-module https://github.com/invoice-x/invoice2data#installation-of-input-modules

 click E https://github.com/invoice-x/invoice2data/blob/master/docs/tutorial.md#options

 click tables https://github.com/invoice-x/invoice2data/blob/master/docs/tutorial.md#tables

 click lines https://github.com/invoice-x/invoice2data/blob/master/docs/tutorial.md#lines

 click regex https://github.com/invoice-x/invoice2data/blob/master/docs/tutorial.md#regex

 click static https://github.com/invoice-x/invoice2data/blob/master/docs/tutorial.md#parser-static

```


## 1. Text Extraction:

Variety of Techniques: invoice2data uses different methods to extract text from PDF invoices. It can utilize tools like pdftotext, pdfminer, or even OCR (Optical Character Recognition) if the PDF is image-based.

## 2. Template Matching:

YAML or JSON Templates: You provide invoice2data with a template that defines the structure of your invoices. This template uses regular expressions (regex) to identify and locate specific pieces of information like invoice number, date, total amount, etc.
Flexible Templates: The template system is designed to be flexible and can handle variations in invoice layouts. You can define static fields, line item patterns, and even use plugins for complex table extraction.

## 3. Data Extraction:

Regex Matching: invoice2data uses the regex patterns in your template to search the extracted text and identify the relevant information.
Data Organization: The extracted data is then organized into a structured format, such as a dictionary or a list, making it easy to work with.

## 4. Output:

Various Formats: You can output the extracted data in different formats like CSV, JSON, or XML.
File Renaming: invoice2data can even rename the PDF files based on the extracted information.
