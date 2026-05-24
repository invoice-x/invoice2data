#!/usr/bin/python
"""Command-line interface."""

import datetime
import logging
import re
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any
from typing import ClassVar

import click

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import read_templates
from invoice2data.extract.template_builder import suggested_template
from invoice2data.extract.template_builder import to_yaml

from .input import INPUT_MODULES
from .input import is_available
from .input import ocrmypdf
from .input import pdfium
from .input import pdftotext
from .input import text
from .output import to_csv
from .output import to_json
from .output import to_xml


logger = logging.getLogger()

# Backend registry lives in invoice2data.input (see input.__interface__).
input_mapping = INPUT_MODULES

#: Default ordered text backends tried when ``input_module`` is not forced.
#: ``pdfium`` (pypdfium2) leads — fast and dependency-light — with ``pdftotext``
#: (poppler ``-layout``, the layout/accuracy anchor) as the fallback. The
#: benchmark (docs/backend-benchmark.md) shows this matches pdftotext's accuracy
#: while running faster: the cascade falls back automatically when pdfium fails
#: to match, misses a required field, or drops a declared line-item table, and
#: layout/area-sensitive templates pin ``input_module: pdftotext`` for the rest.
#: Backends whose dependency is missing are skipped automatically.
DEFAULT_INPUT_READERS = [pdfium, pdftotext]

output_mapping = {
    "csv": to_csv,
    "json": to_json,
    "xml": to_xml,
    "none": None,
}


class Color:
    """A class for terminal color codes."""

    BOLD = "\033[1m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW_BACK = "\033[1;43m"
    RED_BACK = "\033[1;41m"
    BOLD_RED = BOLD + RED
    END = "\033[0m"


class ColorLogFormatter(logging.Formatter):
    """A class for formatting colored logs."""

    FORMAT = (
        "%(prefix)s%(levelname)s:%(suffix)s%(name)s:%(prefix)s %(message)s%(suffix)s"
    )

    LOG_LEVEL_COLOR: ClassVar = {
        "DEBUG": {"prefix": "", "suffix": Color.END},
        "INFO": {"prefix": Color.BLUE, "suffix": Color.END},
        "WARNING": {"prefix": Color.YELLOW_BACK, "suffix": Color.END},
        "ERROR": {"prefix": Color.RED_BACK, "suffix": Color.END},
        "CRITICAL": {"prefix": Color.BOLD_RED, "suffix": Color.END},
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log and console records with colors.

        Format log records with a default prefix and suffix
        to terminal color codes that corresponds
        to the log level name.
        """
        if not hasattr(record, "prefix"):
            record.prefix = self.LOG_LEVEL_COLOR.get(record.levelname.upper(), {}).get(
                "prefix"
            )

        if not hasattr(record, "suffix"):
            record.suffix = self.LOG_LEVEL_COLOR.get(record.levelname.upper(), {}).get(
                "suffix"
            )

        formatter = logging.Formatter(self.FORMAT)
        return formatter.format(record)


stream_handler = logging.StreamHandler()
stream_handler.setFormatter(ColorLogFormatter())
logger.propagate = False

if not logger.handlers:
    logger.addHandler(stream_handler)


def extract_data(  # noqa: C901
    invoicefile: str,
    templates: list[InvoiceTemplate] | None = None,
    input_module: Any = None,
    ai_fallback: bool = False,
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

    Returns:
        dict[str, Any]: Extracted and matched fields, or an empty dict ``{}`` if
            text extraction fails or no template matches.

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
        {'issuer': 'OYO', 'amount': 1939.0, 'date': datetime.datetime(2017, 12, 31, 0, 0), 'invoice_number': 'IBZY2087', 'currency': 'INR', 'hotel_details': ' OYO 4189 Resort Nanganallur', 'date_check_in': datetime.datetime(2017, 12, 31, 0, 0), 'date_check_out': datetime.datetime(2018, 1, 1, 0, 0), 'amount_rooms': 1.0, 'booking_id': 'IBZY2087', 'payment_method': 'Cash at Hotel', 'gstin': '06AABCO6063D1ZQ', 'cin': 'U63090DL2012PTC231770', 'desc': 'Invoice from OYO'}

    """
    templates = templates or read_templates()
    readers = _resolve_readers(invoicefile, input_module)
    # Per-template backend pins apply only in auto (cascade) mode; an explicit
    # input_module forces that backend, pin or not.
    auto = input_module is None
    best: dict[str, Any] | None = None  # complete-but-lineless result, kept as fallback

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

        template = _match_template(extracted_str, templates)
        if template is None:
            continue

        # A template may pin the backend it was authored for (e.g. an area or
        # table template that needs poppler's layout). Honour it by re-extracting
        # with that backend; this also short-circuits straight to the right
        # backend once a faster default leads the cascade. Pins apply in auto
        # mode only — an explicit input_module is taken at face value.
        preferred = _preferred_module(template, used=reader) if auto else None
        if preferred is not None:
            preferred_str = _safe_to_text(preferred, invoicefile)
            preferred_template = (
                _match_template(preferred_str, templates) if preferred_str else None
            )
            if preferred_template is not None:
                reader = preferred
                extracted_str = preferred_str
                template = preferred_template

        logger.info("Using %s template", template["template_name"])
        result = _run_template(template, extracted_str, invoicefile, reader)
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
        extracted_str = module.to_text(invoicefile)
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
        InvoiceTemplate | None: The highest-priority matching template, or
            ``None``. Templates are tried by descending ``priority`` (default 5),
            preserving alphabetical order within the same priority.
    """
    ordered = sorted(templates, key=lambda t: t.get("priority", 5), reverse=True)
    for template in ordered:
        if template.matches_input(extracted_str):
            return template
    return None


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
    template: InvoiceTemplate, extracted_str: str, invoicefile: str, reader: Any
) -> dict[str, Any]:
    """Run a matched template, returning ``{}`` if required fields are missing.

    Args:
        template (InvoiceTemplate): The matched template.
        extracted_str (str): The extracted invoice text.
        invoicefile (str): Path to the invoice file.
        reader (Any): The backend that produced ``extracted_str``.

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


def _sample_text(invoicefile: str, input_module: Any = None) -> str:
    """Return the first non-empty text extracted from a sample file.

    Args:
        invoicefile (str): Path to the sample document.
        input_module (Any): Forced input backend, or None for the cascade.

    Returns:
        str: The extracted text, or ``""`` if every backend failed.
    """
    for reader in _resolve_readers(invoicefile, input_module):
        text = _safe_to_text(reader, invoicefile)
        if text:
            return text
    return ""


def _default_template_path(template: dict[str, Any]) -> str:
    """Derive a default ``<issuer>.yml`` output path from a drafted template.

    Args:
        template (dict[str, Any]): The drafted template.

    Returns:
        str: A slugified ``<issuer>.yml`` filename (``template.yml`` as fallback).
    """
    issuer = str(template.get("issuer") or "template")
    slug = re.sub(r"[^a-z0-9]+", "-", issuer.lower()).strip("-") or "template"
    return f"{slug}.yml"


def _run_new_template(
    sample: str, use_ai: bool, template_out: str | None, input_module: Any
) -> None:
    """Draft a template from a sample document and write it after confirmation.

    Args:
        sample (str): Path to the sample document.
        use_ai (bool): Use the configured AI provider instead of heuristics.
        template_out (str | None): Output path; defaults to ``<issuer>.yml``.
        input_module (Any): Forced input backend, or None for the cascade.

    Raises:
        SystemExit: If no text can be extracted from the sample document.
    """
    text = _sample_text(sample, input_module)
    if not text:
        click.echo(f"Could not extract any text from {sample}", err=True)
        raise SystemExit(1)

    if use_ai:
        from .ai.template_generator import generate_template

        template = generate_template(text)
    else:
        template = suggested_template(text)

    # preview_template is pure regex (no AI) -- reused for both modes.
    from .ai.template_generator import preview_template

    preview = preview_template(template, text)

    click.echo("# Drafted template:\n")
    click.echo(to_yaml(template))
    click.echo("# Preview (values the field regexes capture):")
    if preview:
        for field, value in preview.items():
            click.echo(f"  {field}: {value}")
    else:
        click.echo("  (no fields matched -- edit the regexes before use)")

    out_path = template_out or _default_template_path(template)
    if click.confirm(f"\nWrite template to {out_path}?", default=True):
        Path(out_path).write_text(to_yaml(template), encoding="utf-8")
        click.echo(f"Wrote {out_path}")


@click.command()
@click.option(
    "--input-reader",
    "-i",
    type=click.Choice(list(input_mapping.keys())),
    help="Choose text extraction function. Default: auto-detect between text & pdftotext",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(list(output_mapping.keys())),
    default="none",
    help="Choose output format. Default: none",
)
@click.option(
    "--output-date-format",
    "-d",
    default="%Y-%m-%d",
    help="Choose output date format. Default: %%Y-%%m-%%d (ISO 8601 Date)",
)
@click.option(
    "--output-name",
    "-o",
    default="invoices-output",
    help="Custom name for output file. Extension is added based on chosen format.",
)
@click.option(
    "--csv-lines",
    type=click.Choice(["json", "explode"]),
    default="json",
    help="How the CSV output renders line arrays: 'json' (default) JSON-encodes "
    "them; 'explode' writes one row per line item.",
)
@click.option("--debug", is_flag=True, help="Enable debug information.")
@click.option(
    "--copy", "-c", help="Copy and rename processed PDFs to specified folder."
)
@click.option(
    "--move", "-m", help="Move and rename processed PDFs to specified folder."
)
@click.option(
    "--filename-format",
    default="{date} {invoice_number} {desc}.pdf",
    help="Filename format to use when moving or copying processed PDFs."
    'Default: "{date} {invoice_number} {desc}.pdf"',
)
@click.option(
    "--template-folder",
    "-t",
    type=click.Path(exists=True),
    help="Folder containing invoice templates in yml file. Always adds built-in templates.",
)
@click.option(
    "--exclude-built-in-templates",
    is_flag=True,
    help="Ignore built-in templates.",
)
@click.option(
    "--new-template",
    type=click.Path(exists=True, dir_okay=False),
    help="Draft a new template from a sample document, then exit.",
)
@click.option(
    "--ai",
    "use_ai",
    is_flag=True,
    help="Draft the new template with the configured AI provider "
    "(see INVOICE2DATA_AI_* env vars). Default: deterministic heuristics.",
)
@click.option(
    "--template-out",
    type=click.Path(dir_okay=False),
    help="Path to write the drafted template (default: <issuer>.yml).",
)
@click.option(
    "--ai-fallback",
    is_flag=True,
    help="If no template matches, extract fields with the configured AI provider "
    "(opt-in; see INVOICE2DATA_AI_* env vars).",
)
@click.argument(
    "input_files",
    type=click.File("wb"),
    nargs=-1,
)
@click.version_option()
def main(
    input_reader: str | None,
    output_format: str,
    output_date_format: str,
    output_name: str,
    csv_lines: str,
    debug: bool,
    copy: str | None,
    move: str | None,
    filename_format: str,
    template_folder: str | None,
    exclude_built_in_templates: bool,
    new_template: str | None,
    use_ai: bool,
    template_out: str | None,
    ai_fallback: bool,
    input_files: tuple[Any, ...],
) -> None:
    """Extract data from PDF files and output it in a structured format."""
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)

    if new_template:
        _run_new_template(new_template, use_ai, template_out, input_reader)
        return

    input_module = input_reader
    output_module = output_mapping[output_format]

    templates = _load_templates(template_folder, exclude_built_in_templates)

    output = []
    for f in input_files:
        try:
            res = extract_data(
                f.name,
                templates=templates,
                input_module=input_module,
                ai_fallback=ai_fallback,
            )
            if res:
                logger.info(res)
                output.append(res)

                if copy or move:
                    _process_and_move_copy(
                        f.name, res, copy, move, filename_format
                    )  # Extract file processing and copy/move
        except Exception as e:  # noqa: PERF203
            logger.critical(
                "Invoice2data failed to process %s. \nError message: %s", f.name, e
            )
        finally:
            f.close()

    if output_module is to_csv:
        to_csv.write_to_file(
            output, output_name, output_date_format, lines_mode=csv_lines
        )
    elif output_module is not None:
        output_module.write_to_file(output, output_name, output_date_format)


def _load_templates(
    template_folder: str | None, exclude_built_in_templates: bool
) -> list[Any]:
    """Load templates from the specified folder."""
    templates = []
    if template_folder:
        templates.extend(read_templates(str(Path(template_folder).resolve())))
    if not exclude_built_in_templates:
        templates.extend(read_templates())
    return templates


def _process_and_move_copy(
    filename: str,
    res: dict[str, Any],
    copy: str | None,
    move: str | None,
    filename_format: str,
) -> None:
    """Process the extracted data and copy/move the file."""
    kwargs = deepcopy(res)
    for key, value in kwargs.items():
        if isinstance(value, list) and len(value) >= 1:
            kwargs[key] = value[0]
    for key, value in kwargs.items():
        if isinstance(value, datetime.datetime):
            kwargs[key] = value.strftime("%Y-%m-%d")
    if copy:
        new_filename = filename_format.format(**kwargs)
        shutil.copyfile(filename, Path(copy) / new_filename)
    if move:
        new_filename = filename_format.format(**kwargs)
        shutil.move(filename, str(Path(move) / new_filename))


if __name__ == "__main__":
    main(prog_name="invoice2data")  # pragma: no cover
