"""OpenAI-compatible chat-completions provider (used for Groq and OpenRouter). Talks plain HTTPS via httpx.

UNVERIFIED against the live services until a key is available: the request/response shape follows the public
OpenAI-compatible spec and is covered by transport-mocked tests only.
"""
from __future__ import annotations

import base64
import time

import httpx

from .base import ModelProvider, ProviderError, ProviderResult


class OpenAICompatProvider(ModelProvider):
    def __init__(self, name: str, base_url: str, api_key: str, model: str,
                 extra_headers: dict[str, str] | None = None, client: httpx.Client | None = None,
                 timeout_s: float = 60.0) -> None:
        self.name = name
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._model = model
        self._headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", **(extra_headers or {})}
        self._client = client or httpx.Client(timeout=timeout_s)

    def generate(self, prompt: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> ProviderResult:
        content: list[dict] = [{"type": "text", "text": prompt}]
        if image_bytes:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}})
        body = {"model": self._model, "temperature": 0.2, "messages": [{"role": "user", "content": content}]}
        start = time.perf_counter()
        try:
            resp = self._client.post(self._url, headers=self._headers, json=body)
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} request failed: {type(exc).__name__}: {exc}") from exc
        latency = time.perf_counter() - start
        if resp.status_code != 200:
            raise ProviderError(f"{self.name} request failed: HTTP {resp.status_code}: {resp.text[:300]}")
        try:
            data = resp.json()
            text = (data["choices"][0]["message"]["content"] or "").strip()
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name} returned an unreadable response.") from exc
        if not text:
            raise ProviderError(f"{self.name} returned an empty response (possibly blocked or refused).")
        u = data.get("usage") or {}
        usage = {"prompt_tokens": u.get("prompt_tokens", 0) or 0, "output_tokens": u.get("completion_tokens", 0) or 0}
        return ProviderResult(text=text, model=f"{self.name}:{data.get('model') or self._model}", latency_s=latency, usage=usage)
