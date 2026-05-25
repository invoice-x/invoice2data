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
