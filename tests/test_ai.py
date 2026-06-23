import pytest

from invoice2data.ai import get_provider
from invoice2data.ai import invoice_json_schema
from invoice2data.ai import load_config
from invoice2data.ai.config import AIConfig
from invoice2data.ai.providers.mock import MockProvider
from invoice2data.ai.providers.openai_compatible import OpenAICompatibleProvider


_AI_ENV = [
    "INVOICE2DATA_AI_PROVIDER",
    "INVOICE2DATA_AI_MODEL",
    "INVOICE2DATA_AI_BASE_URL",
    "INVOICE2DATA_AI_API_KEY",
]


def test_load_config_defaults_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _AI_ENV:
        monkeypatch.delenv(key, raising=False)
    config = load_config()
    assert config.provider == "mock"


def test_load_config_uses_vendor_default_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in _AI_ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("INVOICE2DATA_AI_PROVIDER", "deepseek")
    monkeypatch.setenv("INVOICE2DATA_AI_MODEL", "deepseek-chat")
    config = load_config()
    assert config.base_url == "https://api.deepseek.com/v1"


def test_invoice_json_schema_types() -> None:
    schema = invoice_json_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    assert props["amount"] == {"type": "number"}
    assert props["date"] == {"type": "string"}
    assert props["lines"]["type"] == "array"


def test_mock_provider_returns_canned_response() -> None:
    provider = MockProvider({"amount": 10.0})
    assert provider.is_available() is True
    assert provider.extract_structured("anything", {}) == {"amount": 10.0}


def test_get_provider_routes_by_config() -> None:
    assert get_provider(AIConfig("mock", "", None, None)).name == "mock"
    compat = get_provider(
        AIConfig("deepseek", "deepseek-chat", "https://api.deepseek.com/v1", "k")
    )
    assert compat.name == "openai-compatible"


def test_openai_compatible_unavailable_without_config() -> None:
    pytest.importorskip("httpx")
    provider = OpenAICompatibleProvider(AIConfig("openai", "", None, None))
    assert provider.is_available() is False


def test_openai_compatible_extract(monkeypatch: pytest.MonkeyPatch) -> None:
    httpx = pytest.importorskip("httpx")
    captured: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> object:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"amount": 121.0, "date": "2024-05-07"}'}}
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = OpenAICompatibleProvider(
        AIConfig("deepseek", "deepseek-chat", "https://api.deepseek.com/v1", "sekret")
    )
    assert provider.is_available() is True
    result = provider.extract_structured("INVOICE total 121.00", {"type": "object"})

    assert result == {"amount": 121.0, "date": "2024-05-07"}
    assert captured["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sekret"  # type: ignore[index]
    assert captured["json"]["model"] == "deepseek-chat"  # type: ignore[index]
    assert captured["json"]["temperature"] == 0  # type: ignore[index]
