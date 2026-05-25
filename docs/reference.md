# Reference

API reference for using invoice2data as a Python library. For the command-line
interface see the [usage](usage) page.

## Library API

```{eval-rst}
.. autofunction:: invoice2data.extract_data
```

Load templates with {func}`read_templates <invoice2data.extract.loader.read_templates>`
(documented under [Extract → loader](#loader)).

### Exceptions

By default `extract_data` returns `{}` on failure. Pass `raise_on_error=True` to
get a typed exception instead, so a caller can tell *why* extraction failed:

```python
from invoice2data import extract_data, NoTemplateFoundError, RequiredFieldsMissingError

try:
    data = extract_data("invoice.pdf", raise_on_error=True)
except RequiredFieldsMissingError as exc:
    print("matched a template but missing:", exc.fields)
except NoTemplateFoundError:
    print("no template matched")
```

```{eval-rst}
.. automodule:: invoice2data.exceptions
   :members:
```

## Input modules

invoice2data resolves a backend by name or module object. When none is forced it
tries an ordered cascade (see {doc}`how-it-works`) and falls back to OCR. Backends
expose a common interface; those backed by optional dependencies self-exclude via
``is_available()``.

### Backend interface and registry
```{eval-rst}
.. automodule:: invoice2data.input
   :members:
```

### pdfium (default)
```{eval-rst}
.. automodule:: invoice2data.input.pdfium
   :members:
```

### pdftotext
```{eval-rst}
.. automodule:: invoice2data.input.pdftotext
   :members:
```

### text
```{eval-rst}
.. automodule:: invoice2data.input.text
   :members:
```

### pdfplumber
```{eval-rst}
.. automodule:: invoice2data.input.pdfplumber
   :members:
```

### pdfminer
```{eval-rst}
.. automodule:: invoice2data.input.pdfminer_wrapper
   :members:
```

### pdfoxide
```{eval-rst}
.. automodule:: invoice2data.input.pdfoxide
   :members:
```

### hotpdf
```{eval-rst}
.. automodule:: invoice2data.input.hotpdf
   :members:
```

### tesseract (OCR)
```{eval-rst}
.. automodule:: invoice2data.input.tesseract
   :members:
```

### ocrmypdf (OCR)
```{eval-rst}
.. automodule:: invoice2data.input.ocrmypdf
   :members:
```

### docTR (deep-learning OCR)
```{eval-rst}
.. automodule:: invoice2data.input.doctr
   :members:
```

### PaddleOCR (deep-learning OCR)
```{eval-rst}
.. automodule:: invoice2data.input.paddleocr
   :members:
```

### Google Vision (OCR)
```{eval-rst}
.. automodule:: invoice2data.input.gvision
   :members:
```

## Output modules

### csv
```{eval-rst}
.. automodule:: invoice2data.output.to_csv
   :members:
```

### json
```{eval-rst}
.. automodule:: invoice2data.output.to_json
   :members:
```

### xml
```{eval-rst}
.. automodule:: invoice2data.output.to_xml
   :members:
```

### Output streams
```{eval-rst}
.. automodule:: invoice2data.output
   :members:
```

## Extract

### loader
```{eval-rst}
.. automodule:: invoice2data.extract.loader
   :members:
```

### InvoiceTemplate
```{eval-rst}
.. autoclass:: invoice2data.extract.invoice_template.InvoiceTemplate
   :members:
   :no-index:
```

```{note}
``:no-index:`` works around an autodoc quirk where members of a typing-generic
``OrderedDict[str, Any]`` subclass are emitted twice. The methods still render
here; they're internal — the public API is {func}`~invoice2data.extract_data`.
```

### Canonical field schema
```{eval-rst}
.. automodule:: invoice2data.extract.schema
   :members:
```

### Validators
```{eval-rst}
.. automodule:: invoice2data.extract.validators
   :members:
```

### Candidate extraction
```{eval-rst}
.. automodule:: invoice2data.extract.candidates
   :members:
```

### Template suggestions
```{eval-rst}
.. automodule:: invoice2data.extract.suggestions
   :members:
```

### Template builder
```{eval-rst}
.. automodule:: invoice2data.extract.template_builder
   :members:
```

### Date parsing
```{eval-rst}
.. automodule:: invoice2data.extract._dates
   :members:
```

### Regex engine
```{eval-rst}
.. automodule:: invoice2data.extract._regex
   :members:
```

### Plugins

#### tables
```{eval-rst}
.. automodule:: invoice2data.extract.plugins.tables
   :members:
```

#### lines
```{eval-rst}
.. automodule:: invoice2data.extract.plugins.lines
   :members:
```

#### camelot
```{eval-rst}
.. automodule:: invoice2data.extract.plugins.camelot
   :members:
```

### Parsers

#### static
```{eval-rst}
.. automodule:: invoice2data.extract.parsers.static
   :members:
```

#### lines
```{eval-rst}
.. automodule:: invoice2data.extract.parsers.lines
   :members:
```

#### regex
```{eval-rst}
.. automodule:: invoice2data.extract.parsers.regex
   :members:
```

## AI (optional)

The AI subsystem is opt-in and provider-pluggable (cloud LLMs or a local Ollama).
See {doc}`ai` for configuration and usage. Requires the ``ai`` extra.

### Configuration
```{eval-rst}
.. automodule:: invoice2data.ai.config
   :members:
```

### Provider interface
```{eval-rst}
.. automodule:: invoice2data.ai.__interface__
   :members:
```

### LLM fallback extraction
```{eval-rst}
.. automodule:: invoice2data.ai.fallback
   :members:
```

### AI template generation
```{eval-rst}
.. automodule:: invoice2data.ai.template_generator
   :members:
```

### JSON schema
```{eval-rst}
.. automodule:: invoice2data.ai.schema_json
   :members:
```
