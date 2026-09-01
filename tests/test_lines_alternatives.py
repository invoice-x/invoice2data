"""`alternatives:` on the lines parser (#759).

The lines parser already had ``rules:`` for **concatenating** results from
multiple line-parsing sub-blocks (all rules run, results appended). This
adds a parallel ``alternatives:`` key with **first-non-empty-wins**
semantics, so template authors can express "try layout A; if A yields
nothing, fall back to layout B" instead of stuffing two blocks into one
mapping and losing the first to YAML key-collision.
"""

import logging

from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.parsers import lines as lines_parser


_TPL = InvoiceTemplate(
    [
        ("issuer", "test"),
        ("keywords", ["test"]),
        ("exclude_keywords", []),
        ("template_name", "alternatives.yml"),
        (
            "options",
            {
                "currency": "EUR",
                "languages": [],
                "decimal_separator": ".",
                "remove_whitespace": False,
                "remove_accents": False,
                "lowercase": False,
                "date_formats": [],
                "replace": [],
            },
        ),
    ]
)


_ALT_A = {
    "start": r"BEGIN A",
    "end": r"END A",
    "line": r"^(?P<sku>SKU\d+)\s+(?P<qty>\d+)$",
}
_ALT_B = {
    "start": r"BEGIN B",
    "end": r"END B",
    "line": r"^(?P<code>C\d+)\s+(?P<count>\d+)$",
}


_CONTENT_A_ONLY = "\n".join(["BEGIN A", "SKU42 3", "SKU7 1", "END A"])
_CONTENT_B_ONLY = "\n".join(["BEGIN B", "C99 5", "END B"])
_CONTENT_A_AND_B = "\n".join(["BEGIN A", "SKU1 1", "END A", "BEGIN B", "C2 2", "END B"])
_CONTENT_NEITHER = "no relevant markers here at all"


def test_first_alternative_matches_wins() -> None:
    """When both alternatives could match, the first that yields rows wins.

    B is never consulted; results are exactly A's.
    """
    settings = {"line_separator": r"\n", "alternatives": [_ALT_A, _ALT_B]}
    rows = lines_parser.parse(_TPL, "lines", settings, _CONTENT_A_AND_B)
    assert rows == [{"sku": "SKU1", "qty": "1"}]


def test_first_alternative_empty_falls_back_to_second() -> None:
    """A's markers absent -> A yields nothing -> B runs and returns its rows."""
    settings = {"line_separator": r"\n", "alternatives": [_ALT_A, _ALT_B]}
    rows = lines_parser.parse(_TPL, "lines", settings, _CONTENT_B_ONLY)
    assert rows == [{"code": "C99", "count": "5"}]


def test_all_alternatives_empty_returns_empty_list() -> None:
    """No alternative matches -> empty list, not an error."""
    settings = {"line_separator": r"\n", "alternatives": [_ALT_A, _ALT_B]}
    rows = lines_parser.parse(_TPL, "lines", settings, _CONTENT_NEITHER)
    assert rows == []


def test_shared_top_level_keys_merge_into_each_alternative() -> None:
    """A `types:` mapping at the top level applies to whichever alt wins."""
    settings = {
        "line_separator": r"\n",
        "types": {"qty": "int"},
        "alternatives": [_ALT_A, _ALT_B],
    }
    rows = lines_parser.parse(_TPL, "lines", settings, _CONTENT_A_ONLY)
    assert rows == [{"sku": "SKU42", "qty": 3}, {"sku": "SKU7", "qty": 1}]


def test_per_alternative_override_beats_shared_top_level() -> None:
    """An alternative's own key wins over the shared top-level value."""
    # Top-level `line` would match SKU rows; alternative B overrides it to
    # match a completely different shape (Cxx rows), so on B-only content the
    # B alternative wins with its own `line` pattern -- not the shared one.
    settings = {
        "line_separator": r"\n",
        "line": r"^(?P<sku>SKU\d+)\s+(?P<qty>\d+)$",  # shared default
        "alternatives": [
            {"start": r"BEGIN A", "end": r"END A"},  # inherits shared `line`
            {
                "start": r"BEGIN B",
                "end": r"END B",
                "line": r"^(?P<code>C\d+)\s+(?P<count>\d+)$",  # override
            },
        ],
    }
    rows = lines_parser.parse(_TPL, "lines", settings, _CONTENT_B_ONLY)
    assert rows == [{"code": "C99", "count": "5"}]


def test_alternatives_and_rules_together_warns_and_prefers_alternatives(
    caplog: "logging.LogCaptureFixture",
) -> None:
    """`alternatives:` wins over `rules:` at the same level; log a warning."""
    settings = {
        "line_separator": r"\n",
        "rules": [
            # If `rules` were honoured here it would concatenate and return
            # BOTH the A rows AND the B rows.
            _ALT_A,
            _ALT_B,
        ],
        "alternatives": [_ALT_A, _ALT_B],
    }
    with caplog.at_level(logging.WARNING, logger=lines_parser.__name__):
        rows = lines_parser.parse(_TPL, "lines", settings, _CONTENT_A_AND_B)
    # First-non-empty-wins -> only A's row, not A+B concatenated.
    assert rows == [{"sku": "SKU1", "qty": "1"}]
    assert any(
        "'alternatives' takes precedence" in rec.getMessage() for rec in caplog.records
    )


def test_single_mapping_and_rules_still_work_unchanged() -> None:
    """Backward-compat smoke: neither `alternatives:` nor `rules:` -> old path."""
    # Single-mapping path.
    single = {**_ALT_A, "line_separator": r"\n"}
    assert lines_parser.parse(_TPL, "lines", single, _CONTENT_A_ONLY) == [
        {"sku": "SKU42", "qty": "3"},
        {"sku": "SKU7", "qty": "1"},
    ]
    # Rules-concatenate path.
    rules = {
        "line_separator": r"\n",
        "rules": [_ALT_A, _ALT_B],
    }
    assert lines_parser.parse(_TPL, "lines", rules, _CONTENT_A_AND_B) == [
        {"sku": "SKU1", "qty": "1"},
        {"code": "C2", "count": "2"},
    ]
