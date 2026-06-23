"""Conditional mypyc compilation for invoice2data.

Most project metadata lives in ``pyproject.toml``; this file exists only to
optionally compile the hot-path modules into C extensions with mypyc. When the
``INVOICE2DATA_COMPILE_MYPYC`` environment variable is ``"1"`` (set by the
cibuildwheel release job) the listed modules are compiled, producing accelerated
wheels. Otherwise a pure-Python package is built — so the default ``uv build``
and ``pip install`` from sdist stay pure Python.
"""

import os

from setuptools import setup


# ``mypycify`` is only available where mypy is installed, so import it lazily.
if os.environ.get("INVOICE2DATA_COMPILE_MYPYC") == "1":
    from mypyc.build import mypycify


def get_ext_modules() -> list:
    """Return the mypyc extension modules to compile, or an empty list.

    Returns:
        list: ``mypycify(...)`` extensions when compilation is requested,
            otherwise an empty list (pure-Python build).
    """
    if os.environ.get("INVOICE2DATA_COMPILE_MYPYC") != "1":
        print("Skipping mypyc compilation. Building pure Python package...")
        return []

    print("Compiling invoice2data hot paths with mypyc...")
    # Leaf hot-path modules only. Intentionally NOT compiled:
    #   - __main__.py: Click sets attributes on the decorated function object,
    #     which fails on a compiled function.
    #   - invoice_template.py: its OrderedDict subclass + dynamic attributes
    #     don't compile cleanly under mypyc.
    return mypycify(
        [
            "src/invoice2data/extract/utils.py",
            "src/invoice2data/extract/_regex.py",
            "src/invoice2data/extract/parsers/regex.py",
            "src/invoice2data/extract/parsers/lines.py",
            "src/invoice2data/extract/plugins/tables.py",
        ]
    )


setup(ext_modules=get_ext_modules())
