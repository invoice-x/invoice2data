"""Sphinx configuration."""

project = "Invoice2Data"
author = "Manuel Riel"
copyright = "2024, Manuel Riel"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
