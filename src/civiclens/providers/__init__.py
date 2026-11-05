from __future__ import annotations

from ..config import KNOWN_PROVIDERS, ConfigError, Settings, load_settings
from .base import ModelProvider, ProviderError, ProviderResult
from .chain import FallbackChain
from .mock import MockProvider
from .openai_compat import OpenAICompatProvider

GROQ_URL = "https://api.groq.com/openai/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1"


def _build(name: str, s: Settings) -> ModelProvider | None:
    """Build one provider, or None when its key is missing."""
    if name == "groq" and s.groq_api_key:
        return OpenAICompatProvider("groq", GROQ_URL, s.groq_api_key, s.groq_model)
    if name == "openrouter" and s.openrouter_api_key:
        return OpenAICompatProvider("openrouter", OPENROUTER_URL, s.openrouter_api_key, s.openrouter_model,
                                    extra_headers={"X-Title": "CivicLens"},
                                    extra_body=None if s.openrouter_reasoning else {"reasoning": {"enabled": False}})
    if name == "gemini" and s.gemini_api_key:
        # imported lazily: the SDK is only needed when Gemini is in the chain
        from .gemini import GeminiProvider

        return GeminiProvider(s.gemini_api_key, s.gemini_model)
    return None


def get_provider(settings: Settings | None = None) -> ModelProvider:
    """Return the configured provider chain. Mock is used only when explicitly chosen (CIVICLENS_PROVIDER=mock)."""
    s = settings or load_settings()
    unknown = [p for p in s.providers if p not in KNOWN_PROVIDERS]
    if unknown:
        raise ValueError(f"Unknown CIVICLENS_PROVIDER entry: {unknown[0]!r}. Known: {', '.join(KNOWN_PROVIDERS)}")
    if s.providers == ("mock",):
        return MockProvider()
    built = [p for p in (_build(n, s) for n in s.providers if n != "mock") if p is not None]
    if not built:
        raise ConfigError(
            "No AI provider is configured. Set GROQ_API_KEY (primary) and optionally OPENROUTER_API_KEY (fallback) in .env, "
            "or set CIVICLENS_PROVIDER=mock to use the demonstration fallback."
        )
    return built[0] if len(built) == 1 else FallbackChain(built)


__all__ = ["ConfigError", "FallbackChain", "MockProvider", "ModelProvider", "OpenAICompatProvider", "ProviderError",
           "ProviderResult", "get_provider"]
