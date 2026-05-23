"""Deterministic mock provider for tests and offline development.

Returns a preset response without any network call, so the AI plumbing can be
exercised in CI with no API keys.
"""

from typing import Any


class MockProvider:
    """An AIProvider that returns a preset response, ignoring its inputs.

    Args:
        response (dict[str, Any] | None): The dict returned by
            :meth:`extract_structured`. Defaults to an empty dict.
    """

    name = "mock"

    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self._response = response or {}

    def is_available(self) -> bool:
        """Return whether the provider can be used.

        Returns:
            bool: Always True -- the mock needs nothing.
        """
        return True

    def extract_structured(
        self,
        text: str,
        json_schema: dict[str, Any],
        *,
        instructions: str | None = None,
    ) -> dict[str, Any]:
        """Return a copy of the preset response, ignoring the inputs.

        Args:
            text (str): Ignored.
            json_schema (dict[str, Any]): Ignored.
            instructions (str | None): Ignored.

        Returns:
            dict[str, Any]: A shallow copy of the preset response.
        """
        return dict(self._response)
