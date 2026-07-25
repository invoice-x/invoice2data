# Installation

## Dependencies

By default invoice2data extracts text with **[`pypdfium2`](https://github.com/pypdfium2-team/pypdfium2)** —
a self-contained wheel that bundles its own PDF engine, so the common path needs
**no system libraries**. `pip install invoice2data` is enough to get started on
Windows, macOS and Linux.

Some optional backends need extra system tools:

- **`pdftotext`** ([xpdf/poppler-utils](https://poppler.freedesktop.org/)) — better
  at preserving table layout (`-layout`); recommended for layout-sensitive
  templates. Included with macOS Homebrew, Debian and Ubuntu.
- **OCR** — `tesseract` + ImageMagick, or `ocrmypdf` + Ghostscript, for scanned /
  image-only PDFs (see below).



## Installation using pip

invoice2data is delivered by PyPI because it is a convenient way to install the latest version.
However, PyPI and pip cannot address the fact that invoice2data depends on certain non-Python system libraries and programs being installed.


  **Install `invoice2data` using pip**

```bash
pip install invoice2data
```

````{important}
Invoice2data uses a yaml templating system. The yaml templates are loaded with [pyyaml](https://github.com/yaml/pyyaml) which is a pure python implementation. (thus rather slow)
As an alternative json templates can be used. Which are natively better supported by python.
```{tip}
The performance with yaml templates can be greatly increased **10x** 🚀 by using [libyaml](https://github.com/yaml/libyaml)
It can be installed on most distributions by:
`sudo apt-get libyaml-dev`
```
````


## Installation using conda

invoice2data is on [conda-forge](https://anaconda.org/conda-forge/invoice2data):

```bash
conda install -c conda-forge invoice2data
# or, with mamba:
mamba install -c conda-forge invoice2data
```

Conda is the easiest route when you want the OCR system tools handled for you —
`poppler`, `tesseract` and `ghostscript` are all on conda-forge, so nothing else
needs to be installed system-wide. An [`environment.yml`](https://github.com/invoice-x/invoice2data/blob/master/environment.yml)
is also provided in the repository if you want an all-in-one environment with the
common PDF backends and OCR tools pre-installed:

```bash
conda env create -f environment.yml
conda activate invoice2data
```

## Installation of input modules

Most backends are optional and installed via extras. Pick what you need:

```bash
pip install "invoice2data[pdfplumber]"      # pdfplumber backend
pip install "invoice2data[doctr]"           # local deep-learning OCR (docTR)
pip install "invoice2data[paddleocr]"       # local deep-learning OCR (PaddleOCR)
pip install "invoice2data[ai]"              # LLM fallback / template generation
```

| backend | extra | use |
|---------|-------|-----|
| `pdfium` | (built-in) | **default** text extraction, no system deps |
| `text` | (built-in) | already-extracted `.txt` input |
| `pdftotext` | system `poppler` | layout-preserving text |
| `pdfplumber` / `pdfminer` | `pdfplumber` / `pdfminer-six` | pure-Python extraction |
| `tesseract` / `ocrmypdf` | system tools | OCR for scanned PDFs |
| `doctr` / `paddleocr` | `doctr` / `paddleocr` | local deep-learning OCR (privacy-friendly) |
| `gvision` | `googlevision` | Google Cloud Vision OCR |

See {doc}`how-it-works` for the default backend cascade, and {doc}`ai` for the AI
features.

### docTR / PaddleOCR

Local deep-learning OCR backends — good for scans/photos with little
pre-processing, and keep data on your machine. The model weights download on
first run. Select with `--input-reader doctr` or `--input-reader paddleocr`.

### tesseract
An [tesseract](https://github.com/tesseract-ocr/tessdoc/blob/main/FAQ.md#how-do-i-get-tesseract) wrapper is included in auto language mode. It will test your input files against the languages installed on your system. To use it, tesseract and imagemagick needs to be installed.
tesseract supports multiple OCR engine modes. By default, the available engine installed on the system will be used.

**Languages:**

tesseract-ocr recognize more than [100 languages](https://github.com/tesseract-ocr/tessdata)
For Linux users, you can often find packages that provide language packs:

```bash
# Display a list of all Tesseract language packs
apt-cache search tesseract-ocr

# Debian/Ubuntu users
apt-get install tesseract-ocr-chi-sim  # Example: Install Chinese Simplified language pack

# Arch Linux users
pacman -S tesseract-data-eng tesseract-data-deu # Example: Install the English and German language packs
```

### ocrmypdf

Refer to [ocrmypdf documentation](https://ocrmypdf.readthedocs.io/en/latest/index.html)
