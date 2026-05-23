"""Interface for input (text-extraction) backends.

Each input backend is a module in the `input` package and provides at a
minimum a `to_text` function:

    def to_text(path, area_details=None, **kwargs) -> str

It extracts the text of the document at `path` and returns it as a string.

`area_details` (optional) restricts extraction to a region of the page. A
backend declares whether it honours it with a module-level flag (default
False):

    SUPPORTS_AREA = True

A backend may declare an availability check, used so it self-excludes when a
runtime dependency (a Python package or a system binary) is missing:

    def is_available() -> bool

If absent, the backend is assumed to be always available.

Backends are registered by name in `input/__init__.py` (the registry
`INPUT_MODULES`); the name is the value used for the `--input-reader` CLI
option and the `input_module` string argument of `extract_data`.
"""
