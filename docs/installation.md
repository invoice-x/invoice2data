
Installation
============

## Installation of dependencies

Invoice2data depends on [xpdf/poppler-utils](https://poppler.freedesktop.org/) to extract texts from pdf's.

**Install pdftotext**

If possible get the latest [xpdf/poppler-utils](https://poppler.freedesktop.org/) version. It's included with macOS Homebrew, Debian and Ubuntu. Without it, `pdftotext` won't parse tables in PDF correctly.



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


## Installation of input modules

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
