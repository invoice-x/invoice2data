# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/invoice-x/invoice2data/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/invoice2data/\_\_init\_\_.py                      |        6 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/\_\_main\_\_.py                      |      337 |       27 |      132 |       21 |     89% |97-\>102, 102-\>107, 137, 146, 245-\>250, 272, 351-352, 488-\>490, 508-516, 532-\>exit, 541, 569-\>567, 571, 621, 655-657, 672, 680-\>exit, 821, 823, 826, 854-855, 918-\>921, 922-923 |
| src/invoice2data/ai/\_\_init\_\_.py                   |        6 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/ai/\_\_interface\_\_.py              |       18 |        2 |        2 |        0 |     90% |    33, 52 |
| src/invoice2data/ai/config.py                         |       11 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/ai/fallback.py                       |       42 |        3 |       16 |        2 |     91% | 83, 86-87 |
| src/invoice2data/ai/providers/\_\_init\_\_.py         |        0 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/ai/providers/mock.py                 |        9 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/ai/providers/openai\_compatible.py   |       28 |        1 |        4 |        2 |     91% |75, 93-\>95 |
| src/invoice2data/ai/schema\_json.py                   |       13 |        0 |        2 |        0 |    100% |           |
| src/invoice2data/ai/template\_generator.py            |       42 |        3 |       16 |        3 |     90% |76, 83, 134 |
| src/invoice2data/exceptions.py                        |       11 |        0 |        2 |        1 |     92% |   41-\>43 |
| src/invoice2data/extract/\_\_init\_\_.py              |        0 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/extract/\_dates.py                   |       41 |        3 |       10 |        1 |     92% |34-35, 115 |
| src/invoice2data/extract/\_regex.py                   |       24 |        0 |        2 |        0 |    100% |           |
| src/invoice2data/extract/candidates.py                |       58 |        4 |       20 |        3 |     91% |77-78, 112-\>110, 146, 148 |
| src/invoice2data/extract/excalibur.py                 |       35 |        0 |       10 |        0 |    100% |           |
| src/invoice2data/extract/invoice\_template.py         |      241 |       15 |      120 |       14 |     91% |84, 116, 224, 232, 256-\>250, 345, 354-355, 401-\>exit, 404-\>exit, 473-\>468, 480-\>479, 500, 509-510, 527-533, 560-561 |
| src/invoice2data/extract/labels.py                    |       33 |        0 |        6 |        0 |    100% |           |
| src/invoice2data/extract/loader.py                    |       62 |        1 |       20 |        3 |     95% |63-\>61, 112, 116-\>95 |
| src/invoice2data/extract/parsers/\_\_init\_\_.py      |        3 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/extract/parsers/\_\_interface\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/extract/parsers/lines.py             |      132 |        0 |       74 |        5 |     98% |113-\>130, 140-\>142, 208-\>207, 325-\>322, 343-\>350 |
| src/invoice2data/extract/parsers/regex.py             |       73 |        6 |       36 |        4 |     91% |45-46, 52, 99-102, 121 |
| src/invoice2data/extract/parsers/static.py            |        9 |        0 |        2 |        0 |    100% |           |
| src/invoice2data/extract/plugins/\_\_init\_\_.py      |        0 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/extract/plugins/\_\_interface\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/extract/plugins/camelot.py           |       47 |        0 |       16 |        0 |    100% |           |
| src/invoice2data/extract/plugins/lines.py             |        9 |        0 |        2 |        1 |     91% | 46-\>exit |
| src/invoice2data/extract/plugins/tables.py            |       85 |        8 |       48 |        8 |     88% |46, 56, 60-\>59, 62-\>59, 114-115, 148, 198-199, 210 |
| src/invoice2data/extract/schema.py                    |       39 |        1 |       24 |        3 |     94% |136, 185-\>184, 188-\>187 |
| src/invoice2data/extract/suggestions.py               |       19 |        0 |       10 |        0 |    100% |           |
| src/invoice2data/extract/template\_builder.py         |       59 |        3 |       20 |        4 |     91% |49, 129, 164-\>162, 166 |
| src/invoice2data/extract/unece\_uom.py                |       24 |        0 |       16 |        0 |    100% |           |
| src/invoice2data/extract/utils.py                     |       23 |        2 |       16 |        2 |     90% |14-\>31, 29-30 |
| src/invoice2data/extract/validators.py                |       24 |        0 |        6 |        0 |    100% |           |
| src/invoice2data/input/\_\_init\_\_.py                |       36 |        0 |        2 |        0 |    100% |           |
| src/invoice2data/input/\_\_interface\_\_.py           |        0 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/input/doctr.py                       |       32 |        0 |        6 |        0 |    100% |           |
| src/invoice2data/input/gvision.py                     |       55 |        7 |       12 |        4 |     84% |28-29, 62-66, 70, 73, 124 |
| src/invoice2data/input/hotpdf.py                      |       12 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/input/ocrmypdf.py                    |       54 |        7 |       14 |        5 |     79% |74-\>77, 81-87, 117-\>119, 121-\>132, 145-146 |
| src/invoice2data/input/paddleocr.py                   |       38 |        6 |        6 |        0 |     86% | 32, 66-72 |
| src/invoice2data/input/pdfium.py                      |       37 |        0 |        6 |        0 |    100% |           |
| src/invoice2data/input/pdfminer\_wrapper.py           |       30 |        0 |        2 |        0 |    100% |           |
| src/invoice2data/input/pdfoxide.py                    |       12 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/input/pdfplumber.py                  |       18 |        3 |        2 |        0 |     85% |     36-38 |
| src/invoice2data/input/pdftotext.py                   |       67 |        3 |       20 |        1 |     95% |54-55, 165 |
| src/invoice2data/input/tesseract.py                   |       94 |        0 |       20 |        0 |    100% |           |
| src/invoice2data/input/text.py                        |        4 |        0 |        0 |        0 |    100% |           |
| src/invoice2data/output/\_\_init\_\_.py               |       17 |        0 |        4 |        0 |    100% |           |
| src/invoice2data/output/to\_csv.py                    |       45 |        0 |       22 |        0 |    100% |           |
| src/invoice2data/output/to\_json.py                   |       18 |        0 |       10 |        0 |    100% |           |
| src/invoice2data/output/to\_xml.py                    |       39 |        1 |       18 |        2 |     95% |30, 77-\>exit |
| tests/\_\_init\_\_.py                                 |        0 |        0 |        0 |        0 |    100% |           |
| tests/common.py                                       |       17 |        0 |        8 |        0 |    100% |           |
| tests/test\_ai.py                                     |       56 |        0 |        4 |        0 |    100% |           |
| tests/test\_ai\_fallback.py                           |       34 |        1 |        0 |        0 |     97% |        41 |
| tests/test\_area\_extraction.py                       |       32 |        0 |        0 |        0 |    100% |           |
| tests/test\_camelot.py                                |       78 |        6 |        2 |        1 |     91% |   157-165 |
| tests/test\_candidates.py                             |       37 |        0 |        0 |        0 |    100% |           |
| tests/test\_cli.py                                    |      231 |       33 |       64 |        6 |     83% |23, 60-\>59, 154, 183, 210, 383, 393-416, 424-455, 459 |
| tests/test\_cli\_logging.py                           |       32 |        0 |        0 |        0 |    100% |           |
| tests/test\_cross\_page\_lines.py                     |       37 |        0 |        0 |        0 |    100% |           |
| tests/test\_csv\_output.py                            |       28 |        0 |        0 |        0 |    100% |           |
| tests/test\_dates.py                                  |       23 |        0 |        0 |        0 |    100% |           |
| tests/test\_deprecations.py                           |       11 |        0 |        0 |        0 |    100% |           |
| tests/test\_doctr.py                                  |       46 |        0 |        0 |        0 |    100% |           |
| tests/test\_excalibur.py                              |       55 |        0 |        2 |        0 |    100% |           |
| tests/test\_exceptions.py                             |       35 |        0 |        0 |        0 |    100% |           |
| tests/test\_extraction.py                             |       43 |        5 |       20 |        4 |     83% |30-32, 37, 57-\>49, 73 |
| tests/test\_gvision.py                                |       40 |        0 |        0 |        0 |    100% |           |
| tests/test\_input\_interface.py                       |       22 |        0 |        2 |        0 |    100% |           |
| tests/test\_interactive\_template.py                  |       41 |        0 |        0 |        0 |    100% |           |
| tests/test\_invoice\_template.py                      |       79 |        2 |        2 |        1 |     96% |   43, 147 |
| tests/test\_issue\_497.py                             |       17 |        0 |        0 |        0 |    100% |           |
| tests/test\_issue\_535.py                             |       49 |        0 |        0 |        0 |    100% |           |
| tests/test\_issue\_544.py                             |       18 |        0 |        0 |        0 |    100% |           |
| tests/test\_issue\_608.py                             |       34 |        0 |        0 |        0 |    100% |           |
| tests/test\_issue\_618.py                             |       11 |        0 |        0 |        0 |    100% |           |
| tests/test\_issue\_652.py                             |       66 |        1 |        2 |        0 |     99% |       135 |
| tests/test\_labels.py                                 |       42 |        0 |        2 |        0 |    100% |           |
| tests/test\_lib.py                                    |      217 |       18 |       36 |        6 |     91% |37-38, 52, 74-76, 113-115, 147, 239, 254, 288-296, 340 |
| tests/test\_lines\_replace.py                         |       20 |        1 |        0 |        0 |     95% |        12 |
| tests/test\_loader.py                                 |       90 |        0 |        0 |        0 |    100% |           |
| tests/test\_loader\_errors.py                         |       19 |        0 |        0 |        0 |    100% |           |
| tests/test\_main.py                                   |        9 |        0 |        0 |        0 |    100% |           |
| tests/test\_main\_helpers.py                          |       46 |        0 |        0 |        0 |    100% |           |
| tests/test\_ocrmypdf.py                               |       30 |        0 |        0 |        0 |    100% |           |
| tests/test\_output\_stdout.py                         |       20 |        0 |        0 |        0 |    100% |           |
| tests/test\_output\_xml.py                            |       25 |        0 |        0 |        0 |    100% |           |
| tests/test\_paddleocr.py                              |       32 |        0 |        0 |        0 |    100% |           |
| tests/test\_pdf\_backends.py                          |       39 |        0 |        0 |        0 |    100% |           |
| tests/test\_regex\_cache.py                           |       16 |        0 |        0 |        0 |    100% |           |
| tests/test\_regex\_engine.py                          |       16 |        0 |        0 |        0 |    100% |           |
| tests/test\_schema.py                                 |       16 |        0 |        0 |        0 |    100% |           |
| tests/test\_static.py                                 |       10 |        0 |        0 |        0 |    100% |           |
| tests/test\_suggestions.py                            |       15 |        0 |        0 |        0 |    100% |           |
| tests/test\_tax\_lines.py                             |       13 |        0 |        0 |        0 |    100% |           |
| tests/test\_template\_builder.py                      |       40 |        0 |        0 |        0 |    100% |           |
| tests/test\_template\_generator.py                    |       42 |        1 |        0 |        0 |     98% |        63 |
| tests/test\_tesseract.py                              |       97 |        0 |        0 |        0 |    100% |           |
| tests/test\_text\_cache.py                            |       39 |        0 |        0 |        0 |    100% |           |
| tests/test\_unece\_uom.py                             |       45 |        0 |        0 |        0 |    100% |           |
| tests/test\_validators.py                             |       28 |        0 |        0 |        0 |    100% |           |
| **TOTAL**                                             | **4309** |  **174** |  **920** |  **107** | **94%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/invoice-x/invoice2data/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/invoice-x/invoice2data/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/invoice-x/invoice2data/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/invoice-x/invoice2data/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Finvoice-x%2Finvoice2data%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/invoice-x/invoice2data/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.