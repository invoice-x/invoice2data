#!/usr/bin/python
"""Command-line interface.

The library API (``extract_data``, ``Invoice2Data``, backend cascade helpers)
lives in :mod:`invoice2data.api`; this module is now a thin click shell that
imports from there and adds the CLI's ANSI/log-formatter plumbing, argument
parsing, interactive template builder, and file-move helpers. Importing the
library no longer forces ``click`` into the caller's environment.
"""

import datetime
import json
import logging
import os
import re
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any
from typing import ClassVar

import click

from invoice2data.api import DEFAULT_INPUT_READERS
from invoice2data.api import Invoice2Data
from invoice2data.api import extract_data
from invoice2data.api import input_mapping
from invoice2data.extract.loader import read_templates
from invoice2data.extract.template_builder import field_regex
from invoice2data.extract.template_builder import preview_field
from invoice2data.extract.template_builder import set_field_regex
from invoice2data.extract.template_builder import suggested_template
from invoice2data.extract.template_builder import to_yaml

# Private helpers re-exported for backwards compatibility with pre-refactor
# callers (tests + downstream code doing `from invoice2data.__main__ import _foo`).
# New code should import these from :mod:`invoice2data.api`.
# `X as X` = explicit re-export (mypy strict --no-implicit-reexport).
from .api import _by_priority as _by_priority
from .api import _match_template as _match_template
from .api import _preferred_module as _preferred_module
from .api import _resolve_readers as _resolve_readers
from .api import _run_template as _run_template
from .api import _safe_to_text as _safe_to_text
from .api import _sample_text as _sample_text
from .output import to_csv
from .output import to_json
from .output import to_xml


logger = logging.getLogger()

# The names above (``DEFAULT_INPUT_READERS``, ``Invoice2Data``, ``extract_data``,
# ``input_mapping``) are re-exported so any pre-refactor import that reached
# into ``invoice2data.__main__`` keeps working. New code should import from
# :mod:`invoice2data.api`.
__all__ = [
    "DEFAULT_INPUT_READERS",
    "Invoice2Data",
    "extract_data",
    "input_mapping",
    "main",
]

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


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


class PlainLogFormatter(logging.Formatter):
    """Plain log formatter that strips ANSI color codes (for --no-color/NO_COLOR)."""

    def __init__(self) -> None:
        super().__init__("%(levelname)s:%(name)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        """Format the record and strip any ANSI color escape sequences."""
        return _ANSI_RE.sub("", super().format(record))


class JsonLogFormatter(logging.Formatter):
    """Machine-readable JSON log formatter (one object per line, for --in-automation)."""

    def format(self, record: logging.LogRecord) -> str:
        """Render the record as a single-line JSON object (ANSI stripped)."""
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "message": _ANSI_RE.sub("", record.getMessage()),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


stream_handler = logging.StreamHandler()
stream_handler.setFormatter(ColorLogFormatter())
logger.propagate = False

if not logger.handlers:
    logger.addHandler(stream_handler)


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


def _interactive_template(template: dict[str, Any], text: str) -> dict[str, Any]:
    """Walk the user through each drafted field (accept / edit / skip) + additions.

    Shows what each field captures (after cleanup), lets the user keep it, edit its
    regex, or drop it, then offers to add fields the builder did not detect.

    Args:
        template (dict[str, Any]): The drafted template.
        text (str): The sample document text (to preview captures).

    Returns:
        dict[str, Any]: The template with its ``fields`` revised by the user.
    """
    kept: dict[str, Any] = {}
    click.echo("\nReview each field — [Enter] keep, 'e' edit regex, 's' skip:\n")
    for name, spec in template.get("fields", {}).items():
        click.echo(f"  {name}")
        click.echo(f"    regex:    {field_regex(spec)}")
        click.echo(f"    captures: {preview_field(spec, text)!r}")
        choice = click.prompt(f"  keep '{name}'?", default="", show_default=False)
        action = choice.strip().lower()[:1]
        if action == "s":
            continue
        if action == "e":
            spec = set_field_regex(
                spec, click.prompt("    regex", default=field_regex(spec))
            )
            click.echo(f"    now captures: {preview_field(spec, text)!r}")
        kept[name] = spec

    while click.confirm("\nAdd another field?", default=False):
        name = click.prompt("  field name").strip()
        if not name:
            break
        spec = click.prompt("  regex (one capture group)")
        click.echo(f"    captures: {preview_field(spec, text)!r}")
        kept[name] = spec

    template["fields"] = kept
    return template


def _run_new_template(
    sample: str,
    use_ai: bool,
    template_out: str | None,
    input_module: Any,
    interactive: bool = False,
) -> None:
    """Draft a template from a sample document and write it after confirmation.

    Args:
        sample (str): Path to the sample document.
        use_ai (bool): Use the configured AI provider instead of heuristics.
        template_out (str | None): Output path; defaults to ``<issuer>.yml``.
        input_module (Any): Forced input backend, or None for the cascade.
        interactive (bool): Review/edit each field via prompts before writing.

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

    click.echo("# Drafted template:\n")
    click.echo(to_yaml(template))
    click.echo("# Preview (values the field regexes capture):")
    preview = preview_template(template, text)
    if preview:
        for field, value in preview.items():
            click.echo(f"  {field}: {value}")
    else:
        click.echo("  (no fields matched -- edit the regexes before use)")

    if interactive:
        template = _interactive_template(template, text)
        click.echo("\n# Final template:\n")
        click.echo(to_yaml(template))

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
    "--debug-optimized-str",
    is_flag=True,
    help="Print the optimized_str each template is matched against "
    "(for template debugging), without the full --debug noise.",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored log output (also honored via the NO_COLOR env var).",
)
@click.option(
    "--in-automation",
    is_flag=True,
    help="Emit logs as machine-readable JSON (one object per line) for automation.",
)
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
    "--template",
    "template_filter",
    default=None,
    help="Force a specific template by name (case-insensitive substring match). "
    "Useful for debugging why a template doesn't match a document.",
)
@click.option(
    "--explain",
    is_flag=True,
    help="After extraction, print a per-field summary (matched template, "
    "captured values, and any required fields that could not be parsed).",
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
    "--interactive",
    is_flag=True,
    help="With --new-template, review/edit each drafted field via prompts.",
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
def main(  # noqa: C901
    input_reader: str | None,
    output_format: str,
    output_date_format: str,
    output_name: str,
    csv_lines: str,
    debug: bool,
    debug_optimized_str: bool,
    no_color: bool,
    in_automation: bool,
    copy: str | None,
    move: str | None,
    filename_format: str,
    template_folder: str | None,
    exclude_built_in_templates: bool,
    template_filter: str | None,
    explain: bool,
    new_template: str | None,
    use_ai: bool,
    template_out: str | None,
    interactive: bool,
    ai_fallback: bool,
    input_files: tuple[Any, ...],
) -> None:
    """Extract data from PDF files and output it in a structured format."""
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)

    if in_automation:
        stream_handler.setFormatter(JsonLogFormatter())
    elif no_color or "NO_COLOR" in os.environ:
        stream_handler.setFormatter(PlainLogFormatter())

    if debug_optimized_str:
        logging.getLogger("invoice2data.optimized_str").setLevel(logging.DEBUG)

    if new_template:
        _run_new_template(new_template, use_ai, template_out, input_reader, interactive)
        return

    input_module = input_reader
    output_module = output_mapping[output_format]

    templates = _load_templates(template_folder, exclude_built_in_templates)
    if template_filter:
        templates = _filter_templates(templates, template_filter)

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
            if explain:
                _explain(f.name, res)
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


def _filter_templates(templates: list[Any], name: str) -> list[Any]:
    """Restrict to templates whose name contains ``name`` (case-insensitive).

    Args:
        templates (list[Any]): Loaded templates.
        name (str): Substring to match against ``template_name``.

    Returns:
        list[Any]: Matching templates.

    Raises:
        click.UsageError: If no template matches ``name`` -- so
            ``--template acme`` fails loudly rather than silently proceeding
            with zero templates (which would just report "No template for X"
            for every input).
    """
    needle = name.lower()
    matches = [t for t in templates if needle in t.get("template_name", "").lower()]
    if not matches:
        available = sorted(t.get("template_name", "") for t in templates)
        raise click.UsageError(
            f"--template {name!r} matched no template. "
            f"Available: {len(available)} templates; try one of "
            f"{available[:5]}{'...' if len(available) > 5 else ''}"
        )
    logger.debug("--template %s -> %d template(s)", name, len(matches))
    return matches


def _explain(invoice_file: str, result: dict[str, Any]) -> None:
    """Print a per-file summary for ``--explain``.

    Deliberately writes to stdout (not the logger) so it renders cleanly even
    with ``--in-automation`` or ``--no-color`` set. Intended for template
    authoring / debugging, not for machine consumption.

    Args:
        invoice_file (str): Path shown at the top of the block.
        result (dict[str, Any]): The ``extract_data`` return value (may be ``{}``).
    """
    click.echo(f"\n=== {invoice_file} ===")
    if not result:
        click.echo("  no template matched (or every match was missing required fields)")
        return
    template_name = result.get("template_name", "<unknown>")
    click.echo(f"  matched: {template_name}")
    # Group fields: required-first, then everything else. Skip internal keys.
    required = ["issuer", "date", "amount", "invoice_number"]
    printed: set[str] = set()
    for key in required:
        if key in result:
            click.echo(f"    {key:20s} = {result[key]!r}")
            printed.add(key)
        else:
            click.echo(f"    {key:20s} MISSING")
    for key, value in result.items():
        if key in printed or key == "template_name":
            continue
        click.echo(f"    {key:20s} = {value!r}")


#: Characters not allowed in filenames on common filesystems (the Windows set is
#: a superset of POSIX's, so this is cross-platform safe), plus control chars.
_ILLEGAL_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize_filename_part(value: str) -> str:
    """Replace characters illegal in filenames with ``_`` (issue #544).

    Args:
        value (str): A field value substituted into the filename format.

    Returns:
        str: The value with illegal filename characters replaced by ``_``.
    """
    return _ILLEGAL_FS_CHARS.sub("_", value)


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
    # Sanitize field values so illegal filename characters (e.g. the "/" in an
    # invoice number like 123/001/2023) don't break the move/copy path (#544).
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = _sanitize_filename_part(value)
    if copy:
        new_filename = filename_format.format(**kwargs)
        shutil.copyfile(filename, Path(copy) / new_filename)
    if move:
        new_filename = filename_format.format(**kwargs)
        shutil.move(filename, str(Path(move) / new_filename))


if __name__ == "__main__":
    main(prog_name="invoice2data")  # pragma: no cover
