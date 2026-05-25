from abc import ABC, abstractmethod
from typing import Any


class LlmStructuredOutput(ABC):
    """Generic structured-output LLM port.

    Use cases build the prompt and a JSON Schema dict; the adapter routes it
    to whichever LLM and returns parsed JSON. The port is intentionally
    primitive — every additional structured-output use case (bio summary,
    portfolio description summary, anything else) reuses this same method
    with its own prompt + schema.
    """

    @abstractmethod
    def generate(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        """Run ``prompt`` and return the parsed JSON object matching
        ``response_schema`` (a JSON Schema dict). ``schema_name`` is a short
        identifier used in caching and logs; it has no semantic meaning."""
