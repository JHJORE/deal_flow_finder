import json
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types as genai_types

from deal_flow.application.ports.services.llm_structured_output import (
    LlmStructuredOutput,
)
from deal_flow.infrastructure.cache.file_cache import FileCache


class GeminiStructuredOutput(LlmStructuredOutput):
    """Gemini adapter. Wraps the ``google-genai`` SDK and owns its own
    on-disk response cache so repeat calls with the same prompt + schema
    cost nothing.
    """

    def __init__(
        self,
        api_key: str,
        cache_dir: Path,
        model: str = "gemini-3.1-flash-lite",
        refresh: bool = False,
    ) -> None:
        self._api_key = api_key
        self._cache = FileCache(cache_dir)
        self._model = model
        self._refresh = refresh
        self._client: genai.Client | None = None

    def _ensure_client(self) -> genai.Client:
        # Defer instantiation: the SDK constructor errors on an empty key,
        # and we want cache-only calls (and summarize=false routes) to work
        # without a key configured.
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not set. Set it in backend/.env to "
                    "enable bio summarization, or pass summarize=false."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def generate(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        key = FileCache.key_for(
            "gemini_generate",
            model=self._model,
            prompt=prompt,
            schema=response_schema,
            schema_name=schema_name,
        )
        if not self._refresh:
            hit = self._cache.read(key)
            if hit is not None:
                return hit["payload"]

        response = self._ensure_client().models.generate_content(
            model=self._model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        text = response.text or "{}"
        payload = json.loads(text)
        self._cache.write(
            key,
            {
                "op": "gemini_generate",
                "inputs": {
                    "model": self._model,
                    "prompt": prompt,
                    "schema_name": schema_name,
                },
                "payload": payload,
            },
        )
        return payload
