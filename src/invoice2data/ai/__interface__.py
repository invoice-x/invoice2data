"""The AIProvider contract and the provider registry.

Mirrors the input-backend seam (``input/__interface__.py``): a small structural
contract plus a factory that instantiates the configured provider. Optional
provider dependencies are imported lazily inside :func:`get_provider` so importing
this module never requires the ``ai`` extra.
"""

from typing import Any
from typing import Protocol
from typing import runtime_checkable

from .config import AIConfig
from .config import load_config


@runtime_checkable
class AIProvider(Protocol):
    """Structural contract for an AI extraction provider.

    Attributes:
        name (str): Short provider identifier.
    """

    name: str

    def is_available(self) -> bool:
        """Return whether the provider is configured and its deps are present.

        Returns:
            bool: True if :meth:`extract_structured` can be called.
        """
        ...

    def extract_structured(
        self,
        text: str,
        json_schema: dict[str, Any],
        *,
        instructions: str | None = None,
    ) -> dict[str, Any]:
        """Extract structured fields from text, constrained to ``json_schema``.

        Args:
            text (str): The document's extracted text.
            json_schema (dict[str, Any]): JSON Schema the result must match.
            instructions (str | None): Optional system prompt override.

        Returns:
            dict[str, Any]: The structured fields.
        """
        ...


def get_provider(config: AIConfig | None = None) -> AIProvider:
    """Instantiate the configured AI provider.

    Args:
        config (AIConfig | None): Configuration to use; loaded from the
            environment when None.

    Returns:
        AIProvider: A ``MockProvider`` when the provider is "mock", otherwise an
            ``OpenAICompatibleProvider`` (which covers every supported vendor).
    """
    config = config or load_config()
    # Imported lazily so the optional httpx dependency is only needed when used.
    from .providers.mock import MockProvider
    from .providers.openai_compatible import OpenAICompatibleProvider

    if config.provider == "mock":
        return MockProvider()
    return OpenAICompatibleProvider(config)
