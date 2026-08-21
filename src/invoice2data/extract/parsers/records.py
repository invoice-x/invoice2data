"""Common post-processing for parsers that produce record dictionaries."""

from typing import Any


def apply_static_and_defaults(
    records: list[dict[str, Any]], settings: dict[str, Any]
) -> list[dict[str, Any]]:
    """Apply declarative static values and fallbacks to each extracted record.

    ``static`` and ``defaults`` are the preferred mapping forms.  The
    ``static_<field>`` and ``<field>_default`` aliases are retained for
    templates that predate the field-based lines parser.  Static values always
    win; defaults only fill absent or empty values, matching the historic
    lines-plugin behaviour.
    """
    static = {
        key.removeprefix("static_"): value
        for key, value in settings.items()
        if key.startswith("static_")
    }
    # `settings.get("static") or {}` (not `.get("static", {})`) so a bare
    # `static:` in YAML (parses to `None`) doesn't raise `TypeError` on the
    # `.update(None)` below. Same for `defaults`.
    static.update(settings.get("static") or {})

    defaults = {
        key.removesuffix("_default"): value
        for key, value in settings.items()
        if key.endswith("_default")
    }
    defaults.update(settings.get("defaults") or {})

    for record in records:
        for key, value in static.items():
            record[key] = value
        for key, value in defaults.items():
            if not record.get(key):
                record[key] = value
    return records
