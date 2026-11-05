"""Environment-based configuration. Never logs or prints key values."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


@dataclass(frozen=True)
class Settings:
    provider: str
    gemini_model: str
    gemini_api_key: str | None


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        provider=os.getenv("CIVICLENS_PROVIDER", "gemini").strip().lower(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        gemini_api_key=(os.getenv("GEMINI_API_KEY") or "").strip() or None,
    )


def require_gemini_key(settings: Settings) -> str:
    if not settings.gemini_api_key:
        raise ConfigError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add a key, "
            "or set CIVICLENS_PROVIDER=mock to use the demonstration fallback."
        )
    return settings.gemini_api_key
