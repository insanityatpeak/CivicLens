"""Primary provider: Google Gemini via the google-genai SDK. UNVERIFIED until spike runs with a key."""
from __future__ import annotations

import time

from .base import ModelProvider, ProviderError, ProviderResult


class GeminiProvider(ModelProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai  # imported lazily so mock use needs no SDK

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, prompt: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> ProviderResult:
        from google.genai import types

        contents: list = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        contents.append(prompt)
        start = time.perf_counter()
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.2),
            )
        except Exception as exc:  # SDK raises various types; surface one clean error
            raise ProviderError(f"Gemini request failed: {type(exc).__name__}: {exc}") from exc
        latency = time.perf_counter() - start
        text = (resp.text or "").strip()
        if not text:
            raise ProviderError("Gemini returned an empty response (possibly blocked or refused).")
        usage = None
        um = getattr(resp, "usage_metadata", None)
        if um is not None:
            usage = {
                "prompt_tokens": getattr(um, "prompt_token_count", 0) or 0,
                "output_tokens": getattr(um, "candidates_token_count", 0) or 0,
            }
        return ProviderResult(text=text, model=self._model, latency_s=latency, usage=usage)
