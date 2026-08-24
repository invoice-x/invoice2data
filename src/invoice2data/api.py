"""Library API for invoice2data.

Structural refactor for the 1.x line: the API used to live inside
:mod:`invoice2data.__main__`, which forced ``import invoice2data`` to pull in
``click`` and the CLI's ANSI/log-formatter plumbing. This module owns
:func:`extract_data` and the :class:`Invoice2Data` class; :mod:`__main__` is
now a thin click shell that imports from here. Public symbols keep their
existing import paths (``from invoice2data import extract_data``) via
``__init__.py`` re-exports.
"""

import logging
from pathlib import Path
from typing import Any

from .exceptions import NoTemplateFoundError
from .exceptions import RequiredFieldsMissingError
from .extract.invoice_template import InvoiceTemplate
from .extract.loader import read_templates
from .input import INPUT_MODULES
from .input import extract_text
from .input import is_available
from .input import ocrmypdf
from .input import pdfium
from .input import pdftotext
from .input import text


logger = logging.getLogger(__name__)

#: Alias kept for backwards compatibility with call sites that referenced it
#: via ``invoice2data.__main__.input_mapping``. New code should import
#: :data:`invoice2data.input.INPUT_MODULES` directly.
input_mapping = INPUT_MODULES

#: Default ordered text backends tried when ``input_module`` is not forced.
#: ``pdfium`` (pypdfium2) leads -- fast and dependency-light -- with
#: ``pdftotext`` (poppler ``-layout``, the layout/accuracy anchor) as the
#: fallback. The benchmark (docs/backend-benchmark.md) shows this matches
#: pdftotext's accuracy while running faster: the cascade falls back
#: automatically when pdfium fails to match, misses a required field, or drops
#: a declared line-item table, and layout/area-sensitive templates pin
#: ``input_module: pdftotext`` for the rest. Backends whose dependency is
#: missing are skipped automatically.
DEFAULT_INPUT_READERS = [pdfium, pdftotext]


__all__ = [
    "DEFAULT_INPUT_READERS",
    "Invoice2Data",
    "extract_data",
    "input_mapping",
]


def extract_data(  # noqa: C901
    invoicefile: str,
    templates: list[InvoiceTemplate] | None = None,
    input_module: Any = None,
    ai_fallback: bool = False,
    raise_on_error: bool = False,
) -> dict[str, Any]:
    """Extracts structured data from PDF/image invoices.

    This function uses the text extracted from a PDF file or image and
    pre-defined regex templates to find structured data.

    Reads template if no template assigned.
    Required fields are matches from templates.

    Args:
        invoicefile (str): Path of electronic invoice file in PDF, JPEG, PNG
        templates (list[InvoiceTemplate] | None): List of instances of class `InvoiceTemplate`.
                                            Templates are loaded using `read_template` function in `loader.py`.
        input_module (Any, optional): Backend used to extract text from the
            given `invoicefile`, as a module or a registry name (e.g.
            'pdftotext', 'pdfium', 'pdfminer', 'tesseract', 'text'). When
            ``None`` (the default), a cascade of backends
            (``DEFAULT_INPUT_READERS``) is tried in order until one yields a
            template match with all required fields.
        ai_fallback (bool, optional): When True and no template matches (or every
            match is incomplete) and OCR does not help, extract fields with the
            configured AI provider (see ``INVOICE2DATA_AI_*`` env vars). Result is
            tagged ``extraction_method: "ai"``. Opt-in; defaults to False.
        raise_on_error (bool, optional): When True, raise a typed
            :class:`~invoice2data.exceptions.InvoiceProcessingError` on failure
            instead of returning ``{}`` -- ``RequiredFieldsMissingError`` when a
            template matched but a required field could not be parsed, otherwise
            ``NoTemplateFoundError``. Defaults to False (the historical ``{}`` contract).

    Returns:
        dict[str, Any]: Extracted and matched fields, or an empty dict ``{}`` if
            text extraction fails or no template matches (unless
            ``raise_on_error`` is set).

    Raises:
        InvoiceProcessingError: When ``raise_on_error`` is True and extraction
            fails (``RequiredFieldsMissingError`` or ``NoTemplateFoundError``).

    Notes:
        Import the required `input_module` when using invoice2data as a library.
        A template may pin the backend it was authored for with a top-level
        ``input_module:`` key; that backend is then used for that template
        regardless of which one matched it first.

    See Also:
        read_template: Function to load templates.
        InvoiceTemplate: Class representing a single invoice template.

    Examples:
        When using `invoice2data` as a library:

        >>> from invoice2data.input import pdftotext
        >>> extract_data("./tests/compare/oyo.pdf", None, pdftotext)
        {'issuer': 'OYO', 'template_name': 'com.oyo.invoice.yml', 'amount': 1939.0, 'date': datetime.datetime(2017, 12, 31, 0, 0), 'invoice_number': 'IBZY2087', 'currency': 'INR', 'hotel_details': ' OYO 4189 Resort Nanganallur', 'date_check_in': datetime.datetime(2017, 12, 31, 0, 0), 'date_check_out': datetime.datetime(2018, 1, 1, 0, 0), 'amount_rooms': 1.0, 'booking_id': 'IBZY2087', 'payment_method': 'Cash at Hotel', 'gstin': '06AABCO6063D1ZQ', 'cin': 'U63090DL2012PTC231770', 'desc': 'Invoice from OYO'}

    """
    templates = _by_priority(templates or read_templates())
    readers = _resolve_readers(invoicefile, input_module)
    # Per-template backend pins apply only in auto (cascade) mode; an explicit
    # input_module forces that backend, pin or not.
    auto = input_module is None
    best: dict[str, Any] | None = None  # complete-but-lineless result, kept as fallback
    field_errors: list[RequiredFieldsMissingError] = []  # missing-fields reasons (#190)

    for reader in readers:
        extracted_str = _safe_to_text(reader, invoicefile)
        if not extracted_str:
            continue
        logger.debug(
            "START %s result ===========================\n%s",
            reader.__name__,
            extracted_str,
        )
        logger.debug("END %s result =============================", reader.__name__)

        template, extracted_str = _match_template_for_reader(
            extracted_str, templates, invoicefile, reader
        )
        if template is None:
            continue

        # A template may pin the backend it was authored for (e.g. an area or
        # table template that needs poppler's layout). Honour it by re-extracting
        # with that backend; this also short-circuits straight to the right
        # backend once a faster default leads the cascade. Pins apply in auto
        # mode only -- an explicit input_module is taken at face value.
        preferred = _preferred_module(template, used=reader) if auto else None
        if preferred is not None:
            preferred_str = _safe_to_text(preferred, invoicefile)
            preferred_template, preferred_str = _match_template_for_reader(
                preferred_str, templates, invoicefile, preferred
            )
            if preferred_template is not None:
                reader = preferred
                extracted_str = preferred_str
                template = preferred_template

        logger.info("Using %s template", template["template_name"])
        result = _run_template(
            template, extracted_str, invoicefile, reader, field_errors
        )
        if result:
            # A template that declares line items but yields none usually means a
            # layout-less backend dropped the table: keep the result but try the
            # next (layout) backend, which may recover the lines.
            if not auto or not _line_items_missing(template, result):
                return result
            best = best or result
            continue
        # Matched, but a required field was missing: fall through to the next
        # backend in the cascade rather than returning an incomplete result.

    # A complete-but-lineless result beats OCR / nothing.
    if best is not None:
        return best

    # Nothing matched (or every match was incomplete): try OCR as a last resort.
    result = _ocr_last_resort(invoicefile, templates, readers)
    if result:
        return result

    # Opt-in AI fallback: let an LLM extract fields when no template fit.
    ai_result = _ai_last_resort(invoicefile, input_module, ai_fallback)
    if ai_result:
        return ai_result

    logger.error("No template for %s", invoicefile)
    if raise_on_error:
        # A matched-but-incomplete template is a more useful reason than "no
        # template", so prefer the missing-fields error when we have one.
        if field_errors:
            raise field_errors[-1]
        raise NoTemplateFoundError(f"No template matched {invoicefile}")
    return {}


def _ai_last_resort(
    invoicefile: str, input_module: Any, ai_fallback: bool
) -> dict[str, Any]:
    """Try the configured AI provider when no template matched (opt-in).

    Args:
        invoicefile (str): Path to the invoice file.
        input_module (Any): Forced input backend, or None for the cascade.
        ai_fallback (bool): Whether AI fallback is enabled.

    Returns:
        dict[str, Any]: AI-extracted fields, or ``{}`` when disabled/unavailable.
    """
    if not ai_fallback:
        return {}
    from .ai.fallback import ai_fallback_extract

    return ai_fallback_extract(_sample_text(invoicefile, input_module))


def _resolve_readers(invoicefile: str, input_module: Any) -> list[Any]:
    """Return the ordered list of input backends to try for ``invoicefile``.

    Args:
        invoicefile (str): Path to the invoice file.
        input_module (Any): An explicit backend (module or registry name) to
            force a single-backend pass, or ``None`` to use the default cascade.

    Returns:
        list[Any]: Backends to try, in order.
    """
    if isinstance(input_module, str):
        return [input_mapping[input_module]]
    if input_module is not None:
        return [input_module]
    if invoicefile.lower().endswith(".txt"):
        return [text]
    readers = [module for module in DEFAULT_INPUT_READERS if is_available(module)]
    return readers or [pdftotext]


def _safe_to_text(module: Any, invoicefile: str) -> str:
    """Extract text with ``module``, returning ``""`` on any failure.

    Args:
        module (Any): An input backend exposing ``to_text``.
        invoicefile (str): Path to the invoice file.

    Returns:
        str: The extracted text, or ``""`` if extraction failed or was empty.
    """
    try:
        extracted_str = extract_text(module, invoicefile)
    except Exception:
        logger.debug(
            "Backend %s failed to extract text from %s",
            module.__name__,
            invoicefile,
            exc_info=True,
        )
        return ""
    if not isinstance(extracted_str, str) or not extracted_str.strip():
        logger.debug("Backend %s produced no text for %s", module.__name__, invoicefile)
        return ""
    return extracted_str


def _match_template(
    extracted_str: str, templates: list[InvoiceTemplate]
) -> InvoiceTemplate | None:
    """Return the first template whose keywords match the text, else ``None``.

    Args:
        extracted_str (str): The extracted invoice text.
        templates (list[InvoiceTemplate]): Candidate templates.

    Returns:
        InvoiceTemplate | None: The first matching template, or ``None``.
            ``templates`` is expected to be priority-ordered already (see
            :func:`_by_priority`, applied once in ``extract_data``).
    """
    for template in templates:
        if template.matches_input(extracted_str):
            return template
    return None


def _match_template_for_reader(
    extracted_str: str, templates: list[InvoiceTemplate], invoicefile: str, reader: Any
) -> tuple[InvoiceTemplate | None, str]:
    """Match templates, applying the match selector's optional page scope."""
    for template in templates:
        scoped_text = extracted_str
        match = template.get("match")
        # ``pages`` at the template root is the pre-1.1 compatibility form.
        # New templates make the matching scope explicit in ``match.pages``;
        # their fields select their own text independently.
        pages = match.get("pages") if isinstance(match, dict) else template.get("pages")
        if pages is not None:
            try:
                scoped_text = extract_text(reader, invoicefile, pages=pages)
            except (OSError, TypeError, ValueError) as exc:
                logger.debug(
                    "Template %s cannot use pages %r with %s: %s",
                    template["template_name"],
                    pages,
                    reader.__name__,
                    exc,
                )
                continue
        if template.matches_input(scoped_text):
            # A selector-based template may match an envelope while extracting
            # its invoice fields from later pages. Do not leak its match scope
            # into those fields; each field owns its own optional ``pages``.
            return template, extracted_str if isinstance(match, dict) else scoped_text
    return None, extracted_str


def _by_priority(templates: list[InvoiceTemplate]) -> list[InvoiceTemplate]:
    """Order templates by descending ``priority`` (default 5).

    A stable sort, so alphabetical order is preserved within a priority level.
    Done once per ``extract_data`` call rather than on every template match.

    Args:
        templates (list[InvoiceTemplate]): Templates to order.

    Returns:
        list[InvoiceTemplate]: Templates highest-priority first.
    """
    return sorted(templates, key=lambda t: t.get("priority", 5), reverse=True)


def _line_items_missing(template: InvoiceTemplate, output: dict[str, Any]) -> bool:
    """Whether a template declares line items but none were extracted.

    A soft-completeness signal for the cascade: a layout-less backend often
    matches a template and fills the required fields yet produces empty line
    items (the table collapses without column layout). When that happens the
    cascade should try the next backend, which may recover the table.

    Args:
        template (InvoiceTemplate): The matched template.
        output (dict[str, Any]): The extracted fields.

    Returns:
        bool: True if the template declares a ``lines``/``tables`` block (or a
            ``parser: lines`` field) but no non-empty list field was produced.
    """
    declares = (
        "lines" in template
        or "tables" in template
        or any(
            isinstance(field, dict) and field.get("parser") in ("lines", "tables")
            for field in template.get("fields", {}).values()
        )
    )
    if not declares:
        return False
    has_items = any(isinstance(value, list) and value for value in output.values())
    return not has_items


def _preferred_module(template: InvoiceTemplate, used: Any) -> Any:
    """Resolve a template's declared ``input_module`` when it differs from ``used``.

    Args:
        template (InvoiceTemplate): The matched template.
        used (Any): The backend that produced the current text.

    Returns:
        Any: The preferred backend module to re-extract with, or ``None`` when
            the template declares none, declares the one already used, or
            declares one that is unknown or unavailable.
    """
    name = template.get("input_module")
    if not name:
        return None
    module = input_mapping.get(name) if isinstance(name, str) else name
    if module is None:
        logger.warning(
            "Template %s declares unknown input_module %r; ignoring",
            template["template_name"],
            name,
        )
        return None
    if module is used:
        return None
    if not is_available(module):
        logger.warning(
            "Template %s prefers input_module %r, but it is unavailable; using %s",
            template["template_name"],
            name,
            used.__name__,
        )
        return None
    return module


def _run_template(
    template: InvoiceTemplate,
    extracted_str: str,
    invoicefile: str,
    reader: Any,
    errors: list[RequiredFieldsMissingError] | None = None,
) -> dict[str, Any]:
    """Run a matched template, returning ``{}`` if required fields are missing.

    Args:
        template (InvoiceTemplate): The matched template.
        extracted_str (str): The extracted invoice text.
        invoicefile (str): Path to the invoice file.
        reader (Any): The backend that produced ``extracted_str``.
        errors (list[RequiredFieldsMissingError] | None): When given, a missing-fields
            failure is appended here (so the caller can surface why it failed).

    Returns:
        dict[str, Any]: The extracted fields, or ``{}`` when the template matched
            but a required field could not be parsed.
    """
    optimized_str = template.prepare_input(extracted_str)
    try:
        return template.extract(optimized_str, invoicefile, reader)
    except ValueError as exc:
        logger.debug(
            "Template %s matched under %s but extraction was incomplete: %s",
            template["template_name"],
            reader.__name__,
            exc,
        )
        if errors is not None and isinstance(exc, RequiredFieldsMissingError):
            errors.append(exc)
        return {}


def _ocr_last_resort(
    invoicefile: str, templates: list[InvoiceTemplate], readers: list[Any]
) -> dict[str, Any]:
    """Try OCR (ocrmypdf) when the primary backends produced no usable match.

    Args:
        invoicefile (str): Path to the invoice file.
        templates (list[InvoiceTemplate]): Candidate templates.
        readers (list[Any]): Backends already attempted (to avoid repeating).

    Returns:
        dict[str, Any]: Extracted fields from the OCR pass, or ``{}``.
    """
    if not ocrmypdf.ocrmypdf_available() or ocrmypdf in readers:
        return {}
    logger.debug("Primary backends produced no match; falling back to ocrmypdf")
    extracted_str = _safe_to_text(ocrmypdf, invoicefile)
    if not extracted_str:
        return {}
    template = _match_template(extracted_str, templates)
    if template is None:
        return {}
    logger.info("Using %s template (ocrmypdf fallback)", template["template_name"])
    return _run_template(template, extracted_str, invoicefile, ocrmypdf)


def _sample_text(invoicefile: str, input_module: Any = None) -> str:
    """Return the first non-empty text extracted from a sample file.

    Args:
        invoicefile (str): Path to the sample document.
        input_module (Any): Forced input backend, or None for the cascade.

    Returns:
        str: The extracted text, or ``""`` if every backend failed.
    """
    for reader in _resolve_readers(invoicefile, input_module):
        sampled = _safe_to_text(reader, invoicefile)
        if sampled:
            return sampled
    return ""


class Invoice2Data:
    """Object-oriented interface around :func:`extract_data`.

    Holds a reusable set of templates so several invoices can be processed
    without reloading templates each time.

    Args:
        load_built_in_templates (bool): Load the bundled templates on init.
            Defaults to True.
    """

    def __init__(self, load_built_in_templates: bool = True) -> None:
        self.templates: list[InvoiceTemplate] = []
        if load_built_in_templates:
            self.templates += read_templates()

    def read_templates(self, path: str) -> None:
        """Add templates from a user folder to this instance.

        Args:
            path (str): Folder containing .yml/.json templates to load.
        """
        self.templates += read_templates(str(Path(path).resolve()))

    def extract_data(self, path: str, input_module: Any = None) -> dict[str, Any]:
        """Extract data from an invoice using this instance's templates.

        Args:
            path (str): Path to the invoice file.
            input_module (Any): Text-extraction module to use. Defaults to None
                (auto-detect between text and pdftotext).

        Returns:
            dict[str, Any]: Extracted fields, or an empty dict if none matched.
        """
        return extract_data(path, self.templates, input_module)
