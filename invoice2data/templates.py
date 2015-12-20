#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: replace with mighty AI, when ready.

templates = [
                {'keyword': 'QualityHosting',
                 'data': [
                         ('amount', r'Total EUR\s+(\d+,\d+)'),
                         ('invoice_number', r'Rechnung\s+(\d{8})'),
                         ('date', r'\s{2,}(\d+\. .+ \d{4})\s{2,}')
                        ]
                },
                {'keyword': 'Nodisto',
                 'data': [
                         ('amount', r'Amount.*\n.*\$(\d+\.\d+) USD'),
                         ('invoice_number', r'Invoice #(\d+)'),
                         ('date', r'Invoice Date:\s+(\d+/\d+/\d+)')
                        ]
                },
                {'keyword': 'Envato',
                 'data': [
                         ('amount', r'Invoice Total: \$(\d+.\d{2})'),
                         ('invoice_number', r'Invoice No. (\d+)'),
                         ('date', r'Order date: (\d+ \w+ \d+)')
                        ]
                },
                {'keyword': 'Amazon Web Services',
                 'data': [
                         ('amount', r'TOTAL AMOUNT DUE ON.*\$(\d+\.\d+)'),
                         ('invoice_number', r'Invoice Number:\s+(\d+)'),
                         ('date', r'Invoice Date:\s+([a-zA-Z]+ \d+ , \d+)')
                        ]
                },
                {'keyword': 'Amazon EU',
                 'data': [
                         ('amount', r'EUR (\d+,\d+)\n\nMit dieser Warenlieferung'),
                         ('invoice_number', r'Rechnungsnr\. ([A-Z0-9\-]+)'),
                         ('date', r'Lieferdatum/Rechnungsdatum.*(\d{1,2}\. \w+ \d{4})')
                        ]
                },
                {'keyword': 'FR58512277450',  # https://www.captaintrain.com/ TODO in progress
                 'data': [
                         ('invoice_number', r'Billet ([A-Z0-9]+)'),
                        ]
                },
                {'keyword': 'FR 71 343059564',  # http://www.sfr.fr/
                 'data': [
                         ('invoice_number', r'N° facture : ([A-Z0-9\-]+)'),
                         ('date', r'Date de facture : (\d{2}/\d{2}/\d{4})'),
                         ('amount', r'(\d+,\d{2}) € TTC'),
                         ('amount_untaxed', r'(\d+,\d{2}) € HT'),
                         ('description', r'(abonnements, forfaits et options du \d{2}/\d{2} au \d{2}/\d{2})'),
                         ('vat', r'(FR 71 343059564)'),
                        ]
                },
]
