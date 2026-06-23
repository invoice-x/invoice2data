import datetime
from typing import Any

import pytest

from invoice2data import extract_data
from invoice2data.ai.fallback import ai_fallback_extract
from invoice2data.ai.providers.mock import MockProvider


def test_ai_fallback_coerces_and_tags_provenance() -> None:
    canned = {
        "amount": "121.00",
        "date": "2024-05-07",
        "invoice_number": "INV-1",
        "junk": None,
        "blank": "",
    }
    result = ai_fallback_extract("any text", provider=MockProvider(canned))

    assert result["amount"] == 121.0  # coerced to float
    assert isinstance(result["date"], datetime.datetime)  # parsed
    assert result["invoice_number"] == "INV-1"
    assert "junk" not in result and "blank" not in result  # empties dropped
    assert result["extraction_method"] == "ai"  # provenance


def test_ai_fallback_empty_text_returns_empty() -> None:
    assert ai_fallback_extract("", provider=MockProvider({"amount": 1.0})) == {}


class _UnavailableProvider:
    name = "down"

    def is_available(self) -> bool:
        return False

    def extract_structured(
        self, text: str, json_schema: dict[str, Any], *, instructions: str | None = None
    ) -> dict[str, Any]:
        raise AssertionError("should not be called when unavailable")


def test_ai_fallback_skips_unavailable_provider() -> None:
    assert ai_fallback_extract("text", provider=_UnavailableProvider()) == {}


def test_extract_data_uses_ai_fallback_when_no_template_matches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    canned = {"amount": "55.00", "date": "2024-03-01", "invoice_number": "X-1"}
    monkeypatch.setattr(
        "invoice2data.ai.fallback.get_provider", lambda: MockProvider(canned)
    )
    sample = tmp_path / "nomatch.txt"
    sample.write_text("some unrecognized document text 12345", encoding="utf-8")

    # Without the flag, no template matches -> empty result.
    assert extract_data(str(sample)) == {}

    result = extract_data(str(sample), ai_fallback=True)
    assert result["extraction_method"] == "ai"
    assert result["amount"] == 55.0
    assert result["invoice_number"] == "X-1"
