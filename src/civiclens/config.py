"""Environment-based configuration. Never logs or prints key values."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


# Model ids are defaults only and Defaults verified against live catalogues on 2026-11-05 (models rotate; re-check if you get 404); override them in the environment.
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
DEFAULT_OPENROUTER_MODEL = "nvidia/nemotron-3.5-super-vl:free"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
KNOWN_PROVIDERS = ("groq", "openrouter", "gemini", "mock")


@dataclass(frozen=True)
class Settings:
    providers: tuple[str, ...]  # priority order; first is primary, the rest are fallbacks
    gemini_model: str
    gemini_api_key: str | None
    groq_model: str
    groq_api_key: str | None
    openrouter_model: str
    openrouter_api_key: str | None

    @property
    def provider(self) -> str:  # primary provider name
        return self.providers[0]


def _key(name: str) -> str | None:
    return (os.getenv(name) or "").strip() or None


def load_settings() -> Settings:
    load_dotenv()
    raw = os.getenv("CIVICLENS_PROVIDER", "groq,openrouter")
    order = tuple(p.strip().lower() for p in raw.split(",") if p.strip()) or ("groq", "openrouter")
    return Settings(
        providers=order,
        gemini_model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip(),
        gemini_api_key=_key("GEMINI_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip(),
        groq_api_key=_key("GROQ_API_KEY"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip(),
        openrouter_api_key=_key("OPENROUTER_API_KEY"),
    )
