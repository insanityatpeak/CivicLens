"""Language handling (English and Hindi)."""
from __future__ import annotations

SUPPORTED = {"en": "English", "hi": "हिन्दी (Hindi)"}


CATEGORY_LABELS = {
    "en": {
        "pothole_road_damage": "Pothole / road damage",
        "garbage_overflow": "Garbage / overflowing bin",
        "stagnant_water": "Stagnant water",
        "damaged_infrastructure": "Damaged public infrastructure",
        "streetlight_concern": "Streetlight concern",
        "other_civic_issue": "Other civic issue",
        "no_civic_issue": "No civic issue detected",
        "unclear": "Unclear",
    },
    "hi": {
        "pothole_road_damage": "गड्ढा / सड़क की क्षति",
        "garbage_overflow": "कचरा / भरा हुआ कूड़ेदान",
        "stagnant_water": "जमा हुआ पानी",
        "damaged_infrastructure": "क्षतिग्रस्त सार्वजनिक ढांचा",
        "streetlight_concern": "स्ट्रीटलाइट की समस्या",
        "other_civic_issue": "अन्य नागरिक समस्या",
        "no_civic_issue": "कोई नागरिक समस्या नहीं मिली",
        "unclear": "अस्पष्ट",
    },
}


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
