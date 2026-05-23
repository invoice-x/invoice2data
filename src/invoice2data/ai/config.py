"""AI provider configuration, resolved from environment variables.

All settings come from ``INVOICE2DATA_AI_*`` env vars so the core library never
hard-codes credentials. The default provider is ``mock`` (no network), so nothing
AI-related runs unless explicitly configured.
"""

import os
from dataclasses import dataclass


#: Default OpenAI-compatible base URLs for known vendors, so a user only needs to
#: set the provider name + key (DeepSeek/Mistral/Ollama and Gemini's compat
#: endpoint all speak the OpenAI chat-completions API).
VENDOR_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "mistral": "https://api.mistral.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "ollama": "http://localhost:11434/v1",
}


@dataclass(frozen=True)
class AIConfig:
    """Resolved AI configuration.

    Attributes:
        provider (str): Provider key -- "mock" or a vendor name
            (openai/deepseek/mistral/gemini/ollama) routed to the
            OpenAI-compatible provider.
        model (str): Model identifier passed to the provider.
        base_url (str | None): API base URL (vendor default when unset).
        api_key (str | None): API key; not required for local providers (Ollama).
    """

    provider: str
    model: str
    base_url: str | None
    api_key: str | None


def load_config() -> AIConfig:
    """Load AI configuration from ``INVOICE2DATA_AI_*`` environment variables.

    Reads ``INVOICE2DATA_AI_PROVIDER`` (default "mock"), ``..._MODEL``,
    ``..._BASE_URL`` (falls back to the vendor default) and ``..._API_KEY``.

    Returns:
        AIConfig: The resolved configuration.
    """
    provider = os.getenv("INVOICE2DATA_AI_PROVIDER", "mock").lower()
    model = os.getenv("INVOICE2DATA_AI_MODEL", "")
    base_url = os.getenv("INVOICE2DATA_AI_BASE_URL") or VENDOR_BASE_URLS.get(provider)
    api_key = os.getenv("INVOICE2DATA_AI_API_KEY")
    return AIConfig(provider=provider, model=model, base_url=base_url, api_key=api_key)
