# Input-backend benchmark (B2)

Speed vs. extraction accuracy of each text-extraction backend, measured by
`benchmarks/run.py` over the bundled `tests/compare/*.pdf` invoices and their
golden `*.json` outputs. Accuracy is the fraction of golden fields each backend
reproduces *through the matching template* — so it reflects real template
compatibility, not raw text quality. The bundled templates are tuned for
poppler's `pdftotext -layout`.

## Per-backend (each backend in isolation)

| backend     | accuracy | matched | speed (raw `to_text`) |
| ----------- | -------- | ------- | --------------------- |
| pdftotext   | 85.9 %   | 146/170 | 20.6 ms/file          |
| pdfium      | 42.9 %   | 73/170  | **4.2 ms/file**       |
| pdfoxide    | 34.7 %   | 59/170  | 5.4 ms/file           |
| pdfminer    | 24.7 %   | 42/170  | 77.9 ms/file          |
| pdfplumber  | 7.1 %    | 12/170  | 120.9 ms/file         |
| hotpdf      | 4.1 %    | 7/170   | 368.1 ms/file         |

`pdftotext` is the accuracy anchor (its `-layout` mode is what the templates
expect). Among the fast, layout-less backends, **pypdfium2 (`pdfium`) is both the
fastest and the most accurate**, which is why it is the fast-path backend in the
cascade.

## Cascade (end-to-end `extract_data`, incl. fallback)

The cascade tries a fast backend first and falls back to `pdftotext` when a
template fails to match or a required field is missing. Layout/area-sensitive
templates pin `input_module: pdftotext` so they always use poppler.

| cascade order            | accuracy | matched | speed (full extract) |
| ------------------------ | -------- | ------- | -------------------- |
| pdftotext-first          | 85.9 %   | 146/170 | 41.7 ms/file         |
| pdfium-first (no pins)   | 82.4 %   | 140/170 | 19.9 ms/file         |
| **pdfium-first + pins**  | 85.9 %   | 146/170 | 28.3 ms/file         |

Pinning the four layout-sensitive bundled templates (`com.amazon.aws`,
`nl.be.coolblue`, `fr.free.adsl-fiber`, `fr.publicationannoncelegale`) recovers
the full accuracy of the pdftotext default while keeping pypdfium2's speed for
everything else. The 6 fields lost without pins are silent soft-failures
(pypdfium2 matches the template and fills the required fields, but a value —
usually a `lines`/line-item table, or an `area`-based field — is wrong because it
has no layout mode).

## Takeaway

- `pdftotext` stays the accuracy anchor and the cascade's safety net.
- pypdfium2 is the right *fast* backend (speed + best layout-less accuracy, and
  a permissive Apache/BSD licence, unlike AGPL PyMuPDF).
- A pypdfium2-first default is viable **only** if layout/area/table-sensitive
  templates declare `input_module: pdftotext`. Reproduce with
  `python benchmarks/run.py`.
