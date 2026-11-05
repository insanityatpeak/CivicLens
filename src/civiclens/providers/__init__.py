from __future__ import annotations

from ..config import Settings, load_settings, require_gemini_key
from .base import ModelProvider, ProviderError, ProviderResult
from .gemini import GeminiProvider
from .mock import MockProvider


def get_provider(settings: Settings | None = None) -> ModelProvider:
    """Return the configured provider. Mock is used only when explicitly chosen."""
    settings = settings or load_settings()
    if settings.provider == "mock":
        return MockProvider()
    if settings.provider == "gemini":
        return GeminiProvider(require_gemini_key(settings), settings.gemini_model)
    raise ValueError(f"Unknown CIVICLENS_PROVIDER: {settings.provider!r}")


__all__ = ["GeminiProvider", "MockProvider", "ModelProvider", "ProviderError", "ProviderResult", "get_provider"]
