"""Excalibur -> invoice2data template converter."""

import json

import pytest
import yaml  # type: ignore[import-untyped]

from invoice2data.extract.excalibur import excalibur_to_camelot_yaml
from invoice2data.extract.excalibur import excalibur_to_template


def test_single_page_stream_keeps_columns() -> None:
    rule = {
        "flavor": "Stream",  # case-insensitive
        "pages": {
            "1": {
                "table_areas": ["50,700,550,50"],
                "columns": ["100,200,300,400"],
            },
        },
    }
    blocks = excalibur_to_template(rule)
    assert blocks == [
        {
            "table_areas": ["50,700,550,50"],
            "columns": ["100,200,300,400"],
            "pages": "1",
            "flavor": "stream",
        },
    ]


def test_single_page_lattice_drops_columns() -> None:
    # camelot ignores `columns` under lattice; the Excalibur task does too, so
    # the conversion drops it for a clean template diff.
    rule = {
        "flavor": "lattice",
        "pages": {
            "1": {
                "table_areas": ["50,700,550,50"],
                "columns": ["100,200,300,400"],
            },
        },
    }
    [block] = excalibur_to_template(rule)
    assert "columns" not in block
    assert block["table_areas"] == ["50,700,550,50"]
    assert block["flavor"] == "lattice"


def test_multipage_emits_one_block_per_page() -> None:
    rule = {
        "flavor": "stream",
        "pages": {
            "1": {"table_areas": ["A"]},
            "2": {"table_areas": ["B"]},
        },
    }
    blocks = excalibur_to_template(rule)
    assert [b["pages"] for b in blocks] == ["1", "2"]
    assert [b["table_areas"] for b in blocks] == [["A"], ["B"]]


def test_top_level_shared_kwargs_merge_into_each_page() -> None:
    # Mirrors Excalibur's tasks.extract: rule_options keys outside flavor/pages
    # are applied to every page.
    rule = {
        "flavor": "stream",
        "pages": {"1": {"table_areas": ["A"]}, "2": {"table_areas": ["B"]}},
        "row_tol": 5,
        "split_text": True,
    }
    blocks = excalibur_to_template(rule)
    for block in blocks:
        assert block["row_tol"] == 5
        assert block["split_text"] is True


def test_accepts_json_string_input() -> None:
    rule_json = json.dumps(
        {"flavor": "lattice", "pages": {"1": {"table_areas": ["A"]}}}
    )
    [block] = excalibur_to_template(rule_json)
    assert block["pages"] == "1"


def test_bad_json_string_raises_value_error() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        excalibur_to_template("not-json")


def test_non_mapping_input_raises_type_error() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        excalibur_to_template("[1, 2, 3]")


def test_empty_pages_returns_empty_list() -> None:
    assert excalibur_to_template({"flavor": "stream", "pages": {}}) == []


def test_missing_flavor_defaults_to_lattice() -> None:
    [block] = excalibur_to_template({"pages": {"1": {"table_areas": ["A"]}}})
    assert block["flavor"] == "lattice"


def test_yaml_renderer_adds_field_default() -> None:
    rule = {"flavor": "stream", "pages": {"1": {"table_areas": ["A"]}}}
    yaml_text = excalibur_to_camelot_yaml(rule)
    loaded = yaml.safe_load(yaml_text)
    assert loaded == {
        "camelot": [
            {
                "table_areas": ["A"],
                "pages": "1",
                "flavor": "stream",
                "field": "lines",
            },
        ],
    }


def test_yaml_renderer_honors_field_override() -> None:
    rule = {"flavor": "stream", "pages": {"1": {"table_areas": ["A"]}}}
    loaded = yaml.safe_load(excalibur_to_camelot_yaml(rule, field="tax_lines"))
    assert loaded["camelot"][0]["field"] == "tax_lines"


def test_converter_does_not_mutate_caller_dict() -> None:
    rule = {"flavor": "stream", "pages": {"1": {"table_areas": ["A"]}}}
    before = json.dumps(rule, sort_keys=True)
    excalibur_to_template(rule)
    assert json.dumps(rule, sort_keys=True) == before
