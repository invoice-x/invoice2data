"""OpenAI-compatible chat-completions provider.

One provider covers OpenAI, DeepSeek, Mistral, Ollama (local) and Gemini's
compat endpoint -- they all expose the same ``/chat/completions`` API. Uses
``httpx`` (the optional ``ai`` extra) so the core stays dependency-light.
"""

import json
from typing import Any

from ..config import AIConfig


try:
    import httpx

    _HAS_HTTPX = True
except ImportError:  # pragma: no cover - exercised via the ai extra
    _HAS_HTTPX = False


_DEFAULT_INSTRUCTIONS = (
    "You extract structured data from the text of a business document. "
    "Return ONLY a JSON object matching the provided schema. "
    "Use null for any field you cannot find; never invent values."
)


class OpenAICompatibleProvider:
    """Calls any OpenAI-compatible ``/chat/completions`` endpoint via httpx.

    Args:
        config (AIConfig): Provider configuration (base_url, model, api_key).
        timeout (float): Request timeout in seconds. Defaults to 60.
    """

    name = "openai-compatible"

    def __init__(self, config: AIConfig, *, timeout: float = 60.0) -> None:
        self._config = config
        self._timeout = timeout

    def is_available(self) -> bool:
        """Return whether httpx is installed and an endpoint + model are set.

        Returns:
            bool: True if the provider can make a request (an API key is not
                required for local endpoints such as Ollama).
        """
        config = self._config
        return _HAS_HTTPX and bool(config.base_url) and bool(config.model)

    def extract_structured(
        self,
        text: str,
        json_schema: dict[str, Any],
        *,
        instructions: str | None = None,
    ) -> dict[str, Any]:
        """Extract structured fields from text via the chat-completions API.

        Args:
            text (str): The document's extracted text.
            json_schema (dict[str, Any]): JSON Schema the response must match.
            instructions (str | None): System prompt; a sensible default is used
                when None.

        Returns:
            dict[str, Any]: The parsed JSON object returned by the model.

        Raises:
            RuntimeError: If httpx is not installed (install ``invoice2data[ai]``).
        """
        if not _HAS_HTTPX:
            raise RuntimeError(
                "httpx is required for the OpenAI-compatible provider; "
                "install invoice2data[ai]."
            )
        config = self._config
        payload = {
            "model": config.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": instructions or _DEFAULT_INSTRUCTIONS},
                {"role": "user", "content": text},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "invoice", "schema": json_schema},
            },
        }
        headers = {}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        response = httpx.post(
            f"{config.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self._timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data: dict[str, Any] = json.loads(content)
        return data
