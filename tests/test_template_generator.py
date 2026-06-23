from typing import Any

from invoice2data.ai.providers.mock import MockProvider
from invoice2data.ai.template_generator import generate_template
from invoice2data.ai.template_generator import preview_template
from invoice2data.extract.loader import prepare_template


SAMPLE = "ACME Corp\nInvoice number: INV-2024-0042\nDate: 2024-05-07\nTotal: 121.00\n"


def test_generate_template_normalizes_draft() -> None:
    draft = {
        "issuer": "ACME Corp",
        "keywords": "ACME Corp",  # a string is coerced to a list
        "fields": {"invoice_number": r"Invoice number:\s*(\S+)"},
    }
    template = generate_template(SAMPLE, provider=MockProvider(draft))
    assert template["issuer"] == "ACME Corp"
    assert template["keywords"] == ["ACME Corp"]
    assert "invoice_number" in template["fields"]


def test_generate_template_issuer_override() -> None:
    provider = MockProvider({"keywords": ["ACME"], "fields": {}})
    template = generate_template(SAMPLE, provider=provider, issuer="Forced Inc")
    assert template["issuer"] == "Forced Inc"


def test_generated_template_is_loadable() -> None:
    draft = {
        "issuer": "ACME",
        "keywords": ["ACME Corp"],
        "fields": {"date": r"Date:\s*(\S+)"},
    }
    template = generate_template(SAMPLE, provider=MockProvider(draft))
    prepared = prepare_template({**template, "template_name": "acme.yml"})
    assert prepared is not None
    assert prepared["keywords"] == ["ACME Corp"]


def test_preview_template_captures_values() -> None:
    template = {
        "fields": {
            "invoice_number": r"Invoice number:\s*(\S+)",
            "amount": r"Total:\s*([\d.]+)",
            "missing": r"NOPE (\d+)",
        }
    }
    preview = preview_template(template, SAMPLE)
    assert preview["invoice_number"] == "INV-2024-0042"
    assert preview["amount"] == "121.00"
    assert "missing" not in preview


class _CapturingProvider:
    name = "capture"

    def __init__(self) -> None:
        self.content = ""

    def is_available(self) -> bool:
        return True

    def extract_structured(
        self, text: str, json_schema: dict[str, Any], *, instructions: str | None = None
    ) -> dict[str, Any]:
        self.content = text
        return {"keywords": ["ACME"], "fields": {}}


def test_generate_template_grounds_with_candidates() -> None:
    provider = _CapturingProvider()
    generate_template(SAMPLE, provider=provider)
    assert "Detected values (hints)" in provider.content
    assert "2024-05-07" in provider.content  # date candidate fed to the model
