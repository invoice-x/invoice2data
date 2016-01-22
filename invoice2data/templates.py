# -*- coding: utf-8 -*-

# TODO: replace with mighty AI, when ready.

templates = [
                {'keywords': ['QualityHosting'],
                 'data': [
                         ('amount', r'Total EUR\s+(\d+,\d+)'),
                         ('amount_untaxed', r'Total EUR\s+(\d+,\d+)'),
                         ('invoice_number', r'Rechnungsnr\.\s+(\d+)'),
                         ('date', r'\s{2,}(\d+\. .+ \d{4})\s{2,}'),
                         ('vat', r'(DE 232 446 240)'),
                        ]
                },
                {'keywords': ['Nodisto'],
                 'data': [
                         ('amount', r'Amount.*\n.*\$(\d+\.\d+) USD'),
                         ('invoice_number', r'Invoice #(\d+)'),
                         ('date', r'Invoice Date:\s+(\d+/\d+/\d+)'),
                        ]
                },
                {'keywords': ['Envato'],
                 'data': [
                         ('amount', r'Invoice Total: \$(\d+.\d{2})'),
                         ('amount_untaxed', r'Invoice Total: \$(\d+.\d{2})'),
                         ('invoice_number', r'Invoice No. (\d+)'),
                         ('date', r'Order date: (\d+ \w+ \d+)'),
                         ('partner_name', r'(Envato)'),
                        ]
                },
                {'keywords': ['Amazon Web Services'],
                 'data': [
                         ('amount', r'TOTAL AMOUNT DUE ON.*\$(\d+\.\d+)'),
                         ('amount_untaxed', r'TOTAL AMOUNT DUE ON.*\$(\d+\.\d+)'),
                         ('invoice_number', r'Invoice Number:\s+(\d+)'),
                         ('date', r'Invoice Date:\s+([a-zA-Z]+ \d+ , \d+)'),
                         ('partner_name', r'(Amazon Web Services, Inc\.)'),
                        ]
                },
                {'keywords': ['Amazon EU'],  # TODO : adapt for Odoo import
                                          # TODO fix keywords to match only DE
                 'data': [
                         ('amount', r'EUR (\d+,\d+)\n\nMit dieser Warenlieferung'),
                         ('invoice_number', r'Rechnungsnr\. ([A-Z0-9\-]+)'),
                         ('date', r'Lieferdatum/Rechnungsdatum.*(\d{1,2}\. \w+ \d{4})'),
                        ]
                },
                # https://www.captaintrain.com/ TODO in progress
                {'keywords': ['FR58512277450'],
                 'data': [
                         ('invoice_number', r'Billet ([A-Z]+)'),
                         ('amount', r'(\d+,\d{2})'),
                         ('amount_untaxed', r'(\d+,\d{2})'),
                         ('date', r'\d+,\d{2}\D+(\d+\s.+\s\d{4})'),
                         ('description', r'Billet [A-Z]+ − ([^\s{5}])'),
                        ]
                },
                # http://www.sfr.fr/ Mobile phone
                {'keywords': ['FR 71 343059564'],
                 'data': [
                         ('invoice_number', r'N° facture : ([A-Z0-9\-]+)'),
                         ('date', r'Date de facture : (\d{2}/\d{2}/\d{4})'),
                         ('amount', r'(\d+,\d{2}) € TTC'),
                         ('amount_untaxed', r'(\d+,\d{2}) € HT'),
                         ('description', r'(abonnements, forfaits et options du \d{2}/\d{2} au \d{2}/\d{2})'),
                         ('vat', r'(FR 71 343059564)'),
                        ]
                },
                # http://www.sfr.fr/ xDSL/Fiber access
                {'keywords': ['FR 71 343 059 564'],
                 'data': [
                         ('invoice_number', r'N° de Facture\s:\s(\d+)'),
                         ('date', r'Facture du (\d{2}/\d{2}/\d{4})'),
                         ('amount', r'Total facturé pour l’ensemble de votre compte\s+\d+,\d{2}\s+\d+,\d{2}\s+(\d+,\d{2})'),
                         ('amount_untaxed', r'Total facturé pour l’ensemble de votre compte\s+(\d+,\d{2})'),
                         ('vat', r'(FR 71 343 059 564)'),
                        ]
                },
                # http://www.akretion.com/
                {'keywords': ['792 377 731'],
                 'data': [
                        ('amount', r'Total TTC :\s+(\d+,\d{2})'),
                        ('amount_untaxed', r'Total HT :\s+(\d+,\d{2})'),
                        ('invoice_number', r'Facture (\w+)'),
                        ('date', r'(\d{2}/\d{2}/\d{4})'),
                        ('date_due', r'\d{2}/\d{2}/\d{4}.+(\d{2}/\d{2}/\d{4})'),
                        ('siren', r'(792 377 731)'),
                        ]
                },
                # Free mobile
                {'keywords': ['FR25499247138'],
                 'data': [
                    ('vat', r'(FR25499247138)'),
                    ('amount_untaxed', r'Total de la facture HT\s+(\d+.\d{2})'),
                    ('amount', r'\spayer TTC\*\s+(\d+.\d{2})'),
                    # for amount, I avoid the 'à' which is not extracted the same
                    # way depending on the version of poppler-utils
                    ('date', r'Facture no \d+ du (\d+ .+ \d{4})'),
                    # for date to work on months with accents, you need a recent
                    # version of poppler-utils. For example, it works with
                    # version 0.33.0-0ubuntu3, but it doesn't work with version
                    # 0.24.5-2ubuntu4.3
                    ('invoice_number', r'Facture no (\d+)'),
                    ]
                },
                # Free SAS (xDSL/Fiber)
                {'keywords': ['FR 604 219 388 61'],
                 'data': [
                    ('vat', r'(FR 604 219 388 61)'),
                    ('amount_untaxed', r'Total facture\s+(\d+.\d{2})'),
                    ('amount', r'Total facture\s+\d+.\d{2}\s+\d+.\d{2}\s+(\d+.\d{2})'),
                    ('date', r'Facture n°\d+ du (\d+ .+ \d{4})'),
                    ('date_due', r'Date limite de paiement le (\d+ .+ \d{4})'),
                    ('invoice_number', r'Facture n°(\d+)'),
                    ]
                },
                # http://www.bouyguestelecom.fr/
                {'keywords': ['FR 74 397 480 930'],
                'data': [
                    ('vat', r'(FR 74 397 480 930)'),
                    ('amount_untaxed', r'Montant de la facture soumis à TVA\s+(\d+,\d{2})'),
                    ('amount', r'Montant de la facture soumis à TVA\s+\d+,\d{2}\s+(\d+,\d{2})'),
                    ('date', r'Date de facture\s+:\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'N° de facture\s+:\s+(\d+)'),
                    ]
                },
                # Sosh.fr (tested with an invoice of 2013)
                {'keywords': ['sosh.fr'],
                                        # I can't use the SIREN as keywords because
                                        # Orange SA has too many different invoice layouts
                'data': [
                    ('siren', r'(380\s?129\s?866)'),
                    ('invoice_number', r'facture n°\s*(\d+)'),
                    ('date', r'émise le (\d{2}/\d{2}/\d{4})'),
                    ('amount_untaxed', r'total facture\s+(\d+,\d{2})'),
                    ('amount', r'total facture\s+\d+,\d{2}\s+(\d+,\d{2})'),
                    ]
                },
                # Orange Business Services
                {'keywords': ['FR 89 380 129 866', 'www.orange-business.com/ece'],
                'data': [
                    ('siren', r'(380\s?129\s?866)'),
                    ('static_vat', r'(380\s?129\s?866)'),
                    ('invoice_number', r'n°\sde\sfacture\s+:\s+(.+)'),
                    ('date', r'date\sde\sfacture\s+:\s+(\d{2}/\d{2}/\d{2})'),
                    ('date_due', r'prélevé\sà\spartir\sdu\s(\d{2}/\d{2}/\d{4})'),
                    ('amount_untaxed', r'total\sfacture\s\(EUR\sHT\)\s+(\d+,\d{2})'),
                    ('amount', r'somme\sà\spayer\s\(EUR\sTTC\)\s+(\d+,\d{2})'),
                    ]
                },
                # Orange fibre
                {'keywords': ['380 129 866 RCS Paris', 'service clients La fibre'],
                'data': [
                    ('static_siren', '380129866'),
                    ('invoice_number', r'n° de facture\s+:\s+(.+)'),
                    ('date', r'date de facture\s+:\s+(\d{2}/\d{2}/\d{2})'),
                    ('amount_untaxed', r'total auprès d\'Orange\s+(\d+,\d{2})'),
                    ('amount', r'total auprès d\'Orange\s+\d+,\d{2}\s+(\d+,\d{2})'),
                    ]
                },
                # Orange Pro ADSL
                {'keywords': ['FR 89 380 129 866', 'internet pro'],
                'data': [
                    ('static_vat', 'FR 89 380 129 866'),
                    ('static_siren', '380129866'),
                    ('date', r'date de facture\s+:\s+(\d{2}/\d{2}/\d{2})'),
                    ('invoice_number', r'n° de facture\s+:\s+(.+)'),
                    ('amount_untaxed', r'votre facture du \d{2}\.\d{2}\.\d{4}\s+(\d+,\d{2})'),
                    ('amount', r'votre facture du \d{2}\.\d{2}\.\d{4}\s+\d+,\d{2}\s€\sHT\s+(\d+.\d{2})'),
                    ]
                },
                # Orange ligne fixe
                {'keywords': ['FR 89 380 129 866', '1015 : SAV en cas de panne de ligne fixe'],
                'data': [
                    ('static_vat', 'FR 89 380 129 866'),
                    ('static_siren', '380129866'),
                    ('date', r'date de facture\s+:\s+(\d{2}/\d{2}/\d{2})'),
                    ('invoice_number', r'n° de facture\s+:\s+(.+)'),
                    ('amount_untaxed', r'total des abonnements et achats\s+(\d+,\d{2})'),
                    ('amount', r'total des abonnements et achats\s+\d+,\d{2}\s+(\d+,\d{2})'),
                    ]
                },
                # http://www.coriolis.com
                {'keywords': ['FR 86419735741'],
                 # Designed to work on the 2 invoice models: mobile phone and Internet
                'data': [
                    ('vat', r'(FR 86419735741)'),
                    ('invoice_number', 'Facture\s[nº\s]+(\d+)'),
                    ('date', 'Date facture\s+(\d{2}/\d{2}/\d{4})'),
                    ('amount_untaxed', r'TOTAL HT\s+(\d+,\d{2})'),
                    ('amount', r'TOTAL FACTURE TTC\s+(\d+,\d{2})'),
                    ]
                },
                # www.finagaz.fr
                {'keywords': ['FR68582018966'],
                'data': [
                    ('vat', r'(FR68582018966)'),
                    ('date', r'Du\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Du\s+\d{2}/\d{2}/\d{4}\s+N°\s+(\d+)'),
                    ('amount_untaxed', r'TOTAL soumis à TVA\s+(\d+,\d{2})'),
                    ('amount', r'TOTAL TTC EUR\s+(\d+,\d{2})'),
                    ]
                },
                # VINCI Autoroutes
                {'keywords': ['FR 53 572 139 996'],
                'data': [
                    ('vat', r'(FR 53 572 139 996)'),
                    ('date', r'Emise le (\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Facture n°\s+(\w+)'),
                    ('amount_untaxed', r'TVA \(code 1\)\s+(\d+,\d{2})'),
                    # I'm not sure this line will always work well... experience will tell
                    ('amount', r'NET A PAYER TTC\s+(\d+,\d{2})'),
                    ]
                },
                # http://www.saur.com/
                {'keywords': ['FR 28 339 379 984'],
                'data': [
                    ('vat', r'(FR 28 339 379 984)'),
                    ('date', r'FACTURE.+\n.+(\d{2}\s.+\s\d{4})'),
                    ('invoice_number', r'FACTURE N°\s+(\d+)'),
                    ('amount_untaxed', r'HT soumis à TVA\s+:\s+([\d ]+,\d{2})'),
                    ('amount', r'Total facture TTC\s+([\d ]+,\d{2})'),
                    ]
                },
                # La Poste SA
                {'keywords': ['FR 39 356 000 000'],
                'data': [
                    ('vat', r'(FR 39 356 000 000)'),
                    ('date', r'FACTURE\s+(\d{2}/\d{2}/\d{2})'),
                    ('invoice_number', r'FACTURE\s+\d{2}/\d{2}/\d{2}\s+(\d+)'),
                    ('amount_untaxed', r'Total HT:\s+(\d+,\d{2})'),
                    ('amount', r'Total TTC:\s+(\d+,\d{2})'),
                    ]
                },
                # http://www.jpg.fr/
                {'keywords': ['FR 72 997 506 407'],
                'data': [
                    ('vat', r'(FR 72 997 506 407)'),
                    ('date', r'(\d\d?/\d\d?/\d{4})'),
                    ('invoice_number', r'FACTURE N°\s+(\d+\.\s\d+\.\d+)'),
                    ('amount_untaxed', r'\d+,\d{2}\s+\d+,\d{2}\s+(\d+,\d{2})\s+\d+,\d{2}\s+\d+,\d{2}'),
                    ('amount', r'\d+,\d{2}\s+\d+,\d{2}\s+\d+,\d{2}\s+\d+,\d{2}\s+(\d+,\d{2})'),
                    ]
                },
                # EDF Entreprises
                {'keywords': ['EDF Entreprises', 'FR 03 552 081 317'],
                'data': [
                    ('static_vat', 'FR 03 552 081 317'),
                    ('date', r'Facture \d+ du (\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Facture (\d+)'),
                    ('amount_untaxed', r'Montant Hors T.V.A. :\s+([\d ]+,\d{2})'),
                    ('amount', r'Total TTC en euros \(détails au verso\) :\s+([\d ]+,\d{2})'),
                    ]
                },
                # Online SAS
                {'keywords': ['FR 35 433 115 904'],
                'data': [
                    ('vat', r'(FR 35 433 115 904)'),
                    ('date', r'Date de facturation\s+:\s+(\d{2}\s.+\s\d{4})'),
                    ('invoice_number', r'Facture n°\s+(\d+)'),
                    ('amount_untaxed', r'(\d+,\d{2})\sEuros\s+\d+,\d{2}\s\%\s+\d+,\d{2}\sEuros\s+\d+,\d{2}\sEuros'),
                    ('amount', r'\d+,\d{2}\sEuros\s+\d+,\d{2}\s\%\s+\d+,\d{2}\sEuros\s+(\d+,\d{2})\sEuros'),
                    ]
                },
                # My Flying box
                {'keywords': ['FR 83 538 645 227'],
                'data': [
                    ('vat', 'FR 83 538 645 227'),
                    ('date', r'DATE\s+(\d{2}/\d{2}/\d{2})'),
                    ('invoice_number', r'N° DE FACTURE\s+(\d+)'),
                    ('amount_untaxed', r'(\d+,\d{2})\s€\s+\d+,\d{2}\s€\s+\d+,\d{2}\s€'),
                    ('amount', r'\d+,\d{2}\s€\s+\d+,\d{2}\s€\s+(\d+,\d{2})\s€'),
                    ]
                },
                # Futur Telecom
                {'keywords': ['Coordonnées bancaires Futur'],
                'data': [
                    ('static_vat', 'FR 92 444 172 274'),
                    ('date', r'Date facture\s+(\d{2}\s.+\s\d{4})'),
                    ('invoice_number', r'N° facture\s+(\d+)'),
                    ('amount_untaxed', r'Total H.T.\s+(\d+,\d{2})'),
                    ('amount', r'Total T.T.C. \(€\)\s+(\d+,\d{2})'),
                    ]
                },
                # PRIVIANET SARL
                {'keywords': ['FR-50440585297'],
                'data': [
                    ('static_vat', 'FR50440585297'),
                    ('date', r'Nyons,\sle\s\w+\s(\d{2}\s.+\s\d{4})'),
                    ('invoice_number', r'Facture\sn°\s([\d-]+)'),
                    ('amount_untaxed', r'Total HT\s+(\d+.\d{2})'),
                    ('amount', r'Total TTC\s+(\d+.\d{2})'),
                    ]
                },
                # Transports Jean Besson
                {'keywords': ['FR 29775649965'],
                'data': [
                    ('static_vat', 'FR29775649965'),
                    ('date', r'(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'FACTURE\sN°\s?(\d+)'),
                    ('amount_untaxed', r'MONTANT HT APRES MAJORATION\s+:\s+(\d+.\d{2})'),
                    ('amount', r'MONTANT TTC A REGLER EN EUROS\s+(\d+.\d{2})'),
                    ]
                },
                # SAT2Way
                {'keywords': ['FR85444740336'],
                'data': [
                    ('static_vat', 'FR85444740336'),
                    ('date', r'Date\sde\sfacturation\s?:\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Facture\snum\s?:\s+(\w+)'),
                    ('amount_untaxed', r'Sous-total\s+:\s+(\d+.\d{2})'),
                    ('amount', r'Total\s+:\s+(\d+.\d{2})'),
                    ]
                },
                # Exaprint, with OCR...
                {'keywords': ['FR23380353235'],
                'data': [
                    ('static_vat', 'FR23380353235'),
                    ('date', r'Date\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Numéro\s+(\d+)'),
                    ('amount_untaxed', r'20\s\%\s(\d+.\d{2})'),
                    ('amount', r'Montant\s+T.T.C.\s+(\d+.\d{2})'),
                    ]
                },
                # Adobe Ireland (FR)
                {'keywords': ['IE6364992H', 'Facture'],
                'data': [
                    ('static_vat', 'IE6364992H'),
                    ('date', r'Date\sde\sla\sfacture\s?:\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Numéro\sde\sfacture\s?:\s+(\w+)'),
                    ('amount_untaxed', r'Montant net\s+TVA\s+Marchandises\s+\d+.\d{2}\s+(\d+.\d{2})'),
                    ('amount', r'Montant\sTTC\s+(\d+.\d{2})'),
                    ]
                },
                # Hootsuite (FR)
                {'keywords': ['EU826021784', 'Détails de la facturation'],
                'data': [
                    ('static_vat', 'EU826021784'),
                    ('date', r'Date\sde\sfacture\s?:\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'N°\sde\sfacture\s?:\s+(\w+)'),
                    ('amount_untaxed', r'Montant payé\s?:\s+€(\d+,\d{2})'),
                    ('amount', r'Montant payé\s?:\s+€(\d+,\d{2})'),
                    ]
                },
                # Moneo Resto
                {'keywords': ['FR 93 422 721 274'],
                'data': [
                    ('static_vat', 'FR93422721274'),
                    ('date', r'Date\sFacture\s?:\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Facture\s+(.+)'),
                    ('amount_tax', r'Montant\sde\sla\sTVA\s\(20\s?%\)\s+(\d+,\d{2})'),
                    ('amount', r'Total\sTTC\s+(\d+,\d{2})'),
                    ]
                },
                # Mediapart (FR)
                {'keywords': ['FR91500631932', 'Facture'],
                'data': [
                    ('static_vat', 'FR91500631932'),
                    ('date', r'DATE\s+CLIENT\s+\d\/\d\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'Facture\sen\s€\sN°\s+:\s+(\w+)'),
                    ('amount_untaxed', r'H\.T\.\s+:\s+(\d+.\d{2})'),
                    ('amount', r'TOTAL\sTTC\s+(\d+.\d{2})'),
                    ]
                },
                # Office TIMELINE (FR)
                {'keywords': ['Office TIMELINE', 'Facture'],
                'data': [
                    # we don't have any VAT number on the invoice :-(
                    ('static_partner_name', 'Office TIMELINE'),
                    ('date', r'Date\sd’achat\s?:\s+\w+\s(\d+\s.+\d{4})'),
                    ('invoice_number', r'Facture\s+(\w+)'),
                    ('currency_iso', r'Total\spayé\s\((\w{3})\)'),
                    ('amount_tax', r'TVA\s+\$(\d+)'),
                    ('amount', r'Total\spayé\s\(\w{3}\)\s+\$(\d+)'),
                    ]
                },
                # Microsoft Ireland (FR)
                {'keywords': ['IE 8256796 U', 'FACTURE'],
                'data': [
                    ('static_vat', 'IE8256796U'),
                    ('date', r'Date\sdu\sdocument\s?:\s+(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'N°\sde\sfacture\s?:\s+(\w+)'),
                    ('amount_untaxed', r'Total\sdes\sfrais\savant\simpôt\s+(\d+,\d{2})'),
                    ('amount', r'Total\sdes\sfrais\sactuels\s+(\d+,\d{2})'),
                    ]
                },
                # Mention Solutions SAS (FR)
                {'keywords': ['FR 34790841266', 'Facture'],
                'data': [
                    ('static_vat', 'FR34790841266'),
                    ('date', r'Date\s:\s+(\d{2}/\d{2}/\d{2})'),
                    ('invoice_number', r'Facture\s+\#([\w-]+)'),
                    ('amount_untaxed', r'Total\s\(excl\.\sVAT\)\s+(\d+,\d{2})'),
                    ('amount', r'Total\s\(incl\.\sVAT\)\s+(\d+,\d{2})'),
                    ]
                },
                # Go Daddy (FR)
                {'keywords': ['EU826010755', 'FACTURE'],
                'data': [
                    ('static_vat', 'EU826010755'),
                    ('date', r'(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'reçu\s?:\s+(\w+)'),
                    ('amount_tax', r'Taxe\s?:\s+(\d+,\d{2})'),
                    ('amount', r'Total\s?:\s+(\d+,\d{2})'),
                    ]
                },
                # BrowserStack, by BinaryLife Inc.
                #{'keywords': ['support@browserstack.com'],
                #'data': [
                #    ('static_partner_name', 'BinaryLife'),
                #    ('date', r'Dated\s?:\s+(\d+\s\w+,\s\d{4})'),  # we have the issue of th
                #    ('invoice_number', r'Invoice\sID:\s+(\w+)'),
                #    ('amount_untaxed', r'Total\s?:\s+\$(\d+.\d{2})'),
                #    ('amount', r'Total\s?:\s+\$(\d+.\d{2})'),
                #    ('currency_iso', r'all\sprices\sin\s(\w{3})'),
                #    ]
                #},
                # Nexity
                {'keywords': ['487530099', 'NEXITY'],
                'data': [
                    ('static_siren', '487530099'),
                    ('date', r',\sle\s(\d{2}/\d{2}/\d{4})'),
                    ('invoice_number', r'N°\sDE\sCOUPON\s:\s+(\w+)'),
                    ('amount', r'SOLDE\sÀ\sPAYER\s\(en\s€\)\s+([\d ]+,\d{2})'),
                    ('date_start', r'Période\sdu\s(\d{2}/\d{2}/\d{4})\sau\s'),
                    ('date_end', r'Période\sdu\s\d{2}/\d{2}/\d{4}\sau\s(\d{2}/\d{2}/\d{4})'),
                    ]
                },
]
