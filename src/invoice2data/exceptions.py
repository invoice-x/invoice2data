"""Typed exceptions for invoice2data (issue #190).

By default :func:`invoice2data.extract_data` returns ``{}`` on failure (the
historical contract). Pass ``raise_on_error=True`` to get one of these instead,
so a library caller can tell *why* extraction failed and show a useful message.
"""

from collections.abc import Iterable


class InvoiceProcessingError(Exception):
    """Base class for invoice2data extraction failures.

    Only raised when ``extract_data(..., raise_on_error=True)``.
    """


class NoTemplateFoundError(InvoiceProcessingError):
    """No template matched the document under any input backend."""


class RequiredFieldsMissingError(InvoiceProcessingError, ValueError):
    """A template matched but one or more required fields could not be parsed.

    Subclasses :class:`ValueError` so the input-backend cascade's existing
    ``except ValueError`` retry handling keeps working unchanged.

    Args:
        fields (Iterable[str]): Required field names that could not be parsed.
        template_name (str | None): The matched template's name, when known.

    Attributes:
        fields (set[str]): The required field names that could not be parsed.
        template_name (str | None): The template that matched, when known.
    """

    def __init__(self, fields: Iterable[str], template_name: str | None = None) -> None:
        self.fields = set(fields)
        self.template_name = template_name
        message = f"Unable to parse required field(s): {', '.join(sorted(self.fields))}"
        if template_name:
            message += f" (template {template_name})"
        super().__init__(message)


class TemplateSyntaxError(InvoiceProcessingError, ValueError):
    """A template's configuration is malformed (author-side error).

    Raised when a template's ``replace`` block, ``lines`` settings, ``tables``
    keys, a numeric field's decimal-separator setting, or an input backend's
    ``area`` block are missing or ill-formed. Replaces the ``AssertionError``
    raised by pre-1.x versions -- asserts silently vanish under ``python -O``
    and expose an internal invariant class to library callers. Subclasses
    :class:`ValueError` so the input-backend cascade's existing
    ``except ValueError`` retry handling continues to skip a broken template
    gracefully.

    Args:
        message (str): Human-readable description of what is wrong.
        template_name (str | None): The offending template's name, when known.

    Attributes:
        template_name (str | None): The offending template, when known.
    """

    def __init__(self, message: str, template_name: str | None = None) -> None:
        self.template_name = template_name
        if template_name:
            message = f"{message} (template {template_name})"
        super().__init__(message)
