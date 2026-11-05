"""Try providers in order; move to the next one only when a provider call fails (quota, network, refusal)."""
from __future__ import annotations

import logging

from .base import ModelProvider, ProviderError, ProviderResult

log = logging.getLogger("civiclens")


class FallbackChain(ModelProvider):
    name = "chain"

    def __init__(self, providers: list[ModelProvider]) -> None:
        if not providers:
            raise ValueError("FallbackChain needs at least one provider.")
        self.providers = providers

    def generate(self, prompt: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> ProviderResult:
        errors: list[str] = []
        for p in self.providers:
            try:
                return p.generate(prompt, image_bytes, mime_type)
            except ProviderError as exc:
                log.warning("provider %s failed, trying next: %s", p.name, exc)
                errors.append(str(exc))
        raise ProviderError("All providers failed. " + " | ".join(errors))
