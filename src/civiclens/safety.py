"""Grounding validator: rule-based checks of a complaint draft against its evidence.

Heuristic, not a proof of faithfulness. It catches the failure modes we can detect reliably.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .i18n import devanagari_ratio
from .schemas import ComplaintDraft, ImageAnalysis, UserContext

_PHONE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")
_DATES = [
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(
        r"\b(?:\d{1,2}\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,4}\b", re.I
    ),
]
_CONTACT = [re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), re.compile(r"https?://\S+")]
_AUTHORITY = [
    re.compile(p, re.I)
    for p in (
        r"municipal\s+corporation",
        r"\bPWD\b",
        r"public\s+works\s+department",
        r"department\s+of\s+\w+",
        r"nagar\s+nigam",
        r"\bBBMP\b",
        r"\bMCD\b",
        r"नगर\s*निगम",
        r"नगरपालिका",
        r"\w+\s+विभाग",
    )
]
_SUBMITTED = [
    re.compile(p, re.I)
    for p in (r"has been (?:submitted|filed|registered)", r"have (?:submitted|filed)", r"complaint (?:no|number|id)", r"जमा कर दी", r"दर्ज कर दी")
]
_HEDGES = (
    "may", "might", "could", "possibl", "appears", "appear", "likely", "potential", "seems", "suggest",
    "सकता", "सकती", "सकते", "संभव", "शायद", "प्रतीत", "लगता", "लगती",
)


@dataclass
class Issue:
    code: str
    message: str
    where: str = ""


@dataclass
class ValidationReport:
    passed: bool
    issues: list[Issue] = field(default_factory=list)

    def messages(self) -> list[str]:
        return [f"{i.code}: {i.message}" + (f" [{i.where}]" if i.where else "") for i in self.issues]


def _all_text(d: ComplaintDraft) -> list[tuple[str, str]]:
    parts = [("description", d.description), ("public_impact", d.public_impact), ("requested_action", d.requested_action)]
    parts += [("location", d.location or "")]
    parts += [(f"observed_evidence[{i}]", t) for i, t in enumerate(d.observed_evidence)]
    parts += [(f"claim[{i}]", c.statement) for i, c in enumerate(d.claim_sources)]
    return parts


def validate_draft(draft: ComplaintDraft, analysis: ImageAnalysis, ctx: UserContext, expected_language: str | None = None) -> ValidationReport:
    issues: list[Issue] = []
    user_fields = ctx.provided_fields()
    allowed_text = " ".join(user_fields.values()).lower()
    obs = {o.id: o for o in analysis.observations}

    # Required fields and draft label
    if not draft.description.strip():
        issues.append(Issue("missing_field", "description is empty", "description"))
    if not draft.requested_action.strip():
        issues.append(Issue("missing_field", "requested_action is empty", "requested_action"))
    if not draft.is_draft:
        issues.append(Issue("not_draft", "complaint must be marked as a draft"))

    # Source mapping
    if not draft.claim_sources:
        issues.append(Issue("no_sources", "claim_sources is empty; claims are not traceable"))
    mapped = {c.statement.strip() for c in draft.claim_sources}
    for i, c in enumerate(draft.claim_sources):
        src = c.source.strip()
        if src.startswith("user:"):
            if src[5:] not in user_fields:
                issues.append(Issue("bad_source", f"claim cites {src!r} but the user did not provide it", f"claim[{i}]"))
        elif src in obs:
            if obs[src].type == "inferred" and not any(h in c.statement.lower() for h in _HEDGES):
                issues.append(Issue("unhedged_inference", "claim rests on an inferred observation but is not hedged", f"claim[{i}]"))
        else:
            issues.append(Issue("bad_source", f"claim cites unknown source {src!r}", f"claim[{i}]"))
    for i, ev in enumerate(draft.observed_evidence):
        if ev.strip() not in mapped:
            issues.append(Issue("unmapped_evidence", "evidence line has no entry in claim_sources", f"observed_evidence[{i}]"))

    # Location must come from the user
    if "location_text" not in user_fields and draft.location and draft.location.strip():
        issues.append(Issue("invented_location", "location given but the user supplied none", "location"))

    # Forbidden fabricated details (allowed only if the user typed them)
    def appears_in_user_text(s: str) -> bool:
        return s.lower() in allowed_text

    for where, text in _all_text(draft):
        if not text:
            continue
        for m in _PHONE.finditer(text):
            if sum(ch.isdigit() for ch in m.group()) >= 8 and not appears_in_user_text(m.group()):
                issues.append(Issue("invented_phone", f"phone-like number {m.group()!r}", where))
        for rx in _DATES:
            for m in rx.finditer(text):
                if not appears_in_user_text(m.group()):
                    issues.append(Issue("invented_date", f"date {m.group()!r} not provided by user", where))
        for rx in _CONTACT:
            for m in rx.finditer(text):
                if not appears_in_user_text(m.group()):
                    issues.append(Issue("invented_contact", f"contact/link {m.group()!r} not provided by user", where))
        for rx in _AUTHORITY:
            for m in rx.finditer(text):
                if not appears_in_user_text(m.group()):
                    issues.append(Issue("invented_authority", f"authority/department {m.group()!r} not provided by user", where))
        for rx in _SUBMITTED:
            if rx.search(text):
                issues.append(Issue("claims_submission", "draft must not claim it was submitted", where))

    # Language check
    if expected_language == "hi" and devanagari_ratio(draft.description) < 0.5:
        issues.append(Issue("wrong_language", "description is not mostly Devanagari", "description"))
    if expected_language and draft.language != expected_language:
        issues.append(Issue("wrong_language", f"draft language is {draft.language!r}, expected {expected_language!r}"))

    return ValidationReport(passed=not issues, issues=issues)
