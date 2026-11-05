"""Language handling (English and Hindi)."""
from __future__ import annotations

SUPPORTED = {"en": "English", "hi": "हिन्दी (Hindi)"}


def validate_language(code: str) -> str:
    if code not in SUPPORTED:
        raise ValueError(f"Unsupported language {code!r}. Supported: {', '.join(SUPPORTED)}")
    return code


def language_name_for_prompt(code: str) -> str:
    return {"en": "English", "hi": "Hindi (Devanagari script)"}[validate_language(code)]


def devanagari_ratio(text: str) -> float:
    """Share of alphabetic characters that are Devanagari."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "ऀ" <= c <= "ॿ") / len(letters)
