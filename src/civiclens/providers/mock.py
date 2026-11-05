"""DEMONSTRATION FALLBACK. Canned, deterministic output. This is NOT AI and must be labeled as such in any UI.

It exists so the app flow can be walked without an API key. It never looks at the image; the scenario is
chosen explicitly by the user. The complaint text is assembled from templates over the ledger it is given.
"""
from __future__ import annotations

import json
import re

from .base import ModelProvider, ProviderResult

BANNER = "DEMONSTRATION FALLBACK: canned output, not a real AI model response."
SCENARIOS = ("pothole", "unclear", "no_issue")

_HI = {
    "A hole in the road surface": "सड़क की सतह में एक गड्ढा है",
    "Loose gravel around the edge of the hole": "गड्ढे के किनारे ढीले पत्थर पड़े हैं",
    "Vehicles may swerve around it": "वाहन इससे बचकर निकल सकते हैं",
    "A dark wet patch on the ground": "ज़मीन पर एक गीला गहरा धब्बा है",
}
_CATEGORY_HI = {
    "pothole_road_damage": "गड्ढा / सड़क की क्षति",
    "unclear": "अस्पष्ट",
    "other_civic_issue": "अन्य नागरिक समस्या",
}


def _analysis(scenario: str) -> dict:
    if scenario == "no_issue":
        return {"category": "no_civic_issue", "category_confidence": "high", "is_civic_issue": False,
                "observations": [{"id": "o1", "text": "A clear street with no visible damage or waste", "type": "observed", "confidence": "high"}],
                "risks_visible": [], "missing_info": [], "clarifying_question": None, "privacy_flags": []}
    if scenario == "unclear":
        return {"category": "unclear", "category_confidence": "low", "is_civic_issue": True,
                "observations": [{"id": "o1", "text": "A dark wet patch on the ground", "type": "observed", "confidence": "medium"}],
                "risks_visible": [], "missing_info": ["what the patch is", "exact location"],
                "clarifying_question": "Is the dark patch water, oil, or something else?", "privacy_flags": []}
    return {"category": "pothole_road_damage", "category_confidence": "high", "is_civic_issue": True,
            "observations": [
                {"id": "o1", "text": "A hole in the road surface", "type": "observed", "confidence": "high"},
                {"id": "o2", "text": "Loose gravel around the edge of the hole", "type": "observed", "confidence": "medium"},
                {"id": "o3", "text": "Vehicles may swerve around it", "type": "inferred", "confidence": "medium"}],
            "risks_visible": [], "missing_info": ["exact location", "how long it has been there"],
            "clarifying_question": None, "privacy_flags": []}


def _grab(prompt: str, label: str) -> str:
    m = re.search(rf"^{re.escape(label)}\s*(.*)$", prompt, re.M)
    return m.group(1).strip() if m else ""


def _complaint(prompt: str) -> dict:
    hi = "Hindi" in prompt
    category = _grab(prompt, "Issue category:")
    ledger = json.loads(_grab(prompt, "Evidence ledger (JSON):") or "[]")
    user = json.loads(_grab(prompt, "User facts (JSON):") or "{}")
    tr = (lambda t: _HI.get(t, t)) if hi else (lambda t: t)
    claims, evidence, missing = [], [], []
    for o in ledger:
        if o["type"] == "observed":
            t = tr(o["text"])
            evidence.append(t)
            claims.append({"statement": t, "source": o["id"]})
    inferred = [o for o in ledger if o["type"] == "inferred"]
    impact = ""
    if inferred:
        o = inferred[0]
        impact = tr(o["text"]) + ("; इससे जोखिम हो सकता है।" if hi else ", which could be unsafe.")
        claims.append({"statement": impact, "source": o["id"]})
    location = user.get("location_text")
    if location:
        claims.append({"statement": location, "source": "user:location_text"})
    else:
        missing.append("location")
    if hi:
        desc = f"मैं एक नागरिक समस्या ({_CATEGORY_HI.get(category, 'नागरिक समस्या')}) की ओर ध्यान दिलाना चाहता/चाहती हूँ।"
        if user.get("ongoing") == "yes":
            desc += " समस्या अभी भी बनी हुई है।"
        action = "कृपया स्थान का निरीक्षण कर मरम्मत या सफाई की व्यवस्था करें।"
    else:
        desc = f"I would like to bring a civic issue to attention ({category.replace('_', ' ')})."
        if user.get("ongoing") == "yes":
            desc += " The problem is reported as ongoing."
        action = "Please inspect the location and arrange for repair or cleanup."
    return {"description": desc, "location": location, "observed_evidence": evidence, "public_impact": impact,
            "requested_action": action, "claim_sources": claims, "missing_info": missing}


class MockProvider(ModelProvider):
    name = "mock"
    is_fallback = True

    def __init__(self, scenario: str = "pothole") -> None:
        self.scenario = scenario

    def generate(self, prompt: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> ProviderResult:
        if "analysing a photo" in prompt:
            text = json.dumps(_analysis(self.scenario))
        elif "write a citizen's complaint DRAFT" in prompt:
            text = json.dumps(_complaint(prompt), ensure_ascii=False)
        else:
            text = f"[{BANNER}] Received prompt of {len(prompt)} chars" + (f" and image of {len(image_bytes)} bytes." if image_bytes else ".")
        return ProviderResult(text=text, model="mock", latency_s=0.0, usage=None, is_fallback=True)
