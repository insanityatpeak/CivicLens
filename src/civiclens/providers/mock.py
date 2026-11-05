"""DEMONSTRATION FALLBACK. Returns canned text. This is NOT AI output and must be labeled as such in any UI."""
from __future__ import annotations

from .base import ModelProvider, ProviderResult

BANNER = "DEMONSTRATION FALLBACK: canned output, not a real AI model response."


class MockProvider(ModelProvider):
    name = "mock"
    is_fallback = True

    def generate(self, prompt: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> ProviderResult:
        text = f"[{BANNER}] Received prompt of {len(prompt)} chars" + (
            f" and image of {len(image_bytes)} bytes." if image_bytes else "."
        )
        return ProviderResult(text=text, model="mock", latency_s=0.0, usage=None, is_fallback=True)
