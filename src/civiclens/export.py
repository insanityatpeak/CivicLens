"""Turn a ComplaintDraft into plain text / markdown for editing and download."""
from __future__ import annotations

from .schemas import ComplaintDraft

_LABELS = {
    "en": {"title": "COMPLAINT DRAFT (not submitted anywhere)", "location": "Location", "not_given": "Not provided",
           "evidence": "What the photo shows", "impact": "Why it matters", "action": "Request", "missing": "Details still missing"},
    "hi": {"title": "शिकायत का मसौदा (कहीं जमा नहीं किया गया)", "location": "स्थान", "not_given": "उपलब्ध नहीं",
           "evidence": "फ़ोटो में क्या दिखता है", "impact": "यह क्यों महत्वपूर्ण है", "action": "अनुरोध", "missing": "अभी भी अनुपलब्ध जानकारी"},
}


def draft_to_text(d: ComplaintDraft) -> str:
    L = _LABELS[d.language]
    lines = [L["title"], "", d.description.strip(), "", f"{L['location']}: {d.location or L['not_given']}"]
    if d.observed_evidence:
        lines += ["", f"{L['evidence']}:"] + [f"- {e}" for e in d.observed_evidence]
    if d.public_impact.strip():
        lines += ["", f"{L['impact']}: {d.public_impact.strip()}"]
    lines += ["", f"{L['action']}: {d.requested_action.strip()}"]
    if d.missing_info:
        lines += ["", f"{L['missing']}: " + ", ".join(d.missing_info)]
    return "\n".join(lines) + "\n"


def text_to_markdown(text: str) -> str:
    head, _, rest = text.partition("\n")
    return f"# {head}\n{rest}"


def to_txt_bytes(text: str) -> bytes:
    """UTF-8 with BOM so Hindi opens correctly in Windows Notepad."""
    return text.encode("utf-8-sig")
