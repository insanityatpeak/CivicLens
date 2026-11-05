"""Typed data models for the pipeline."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]
ObsType = Literal["observed", "inferred"]
Language = Literal["en", "hi"]
Category = Literal[
    "pothole_road_damage",
    "garbage_overflow",
    "stagnant_water",
    "damaged_infrastructure",
    "streetlight_concern",
    "other_civic_issue",
    "no_civic_issue",
    "unclear",
]
PrivacyFlag = Literal["faces", "license_plates"]


class Observation(BaseModel):
    id: str = Field(pattern=r"^o\d+$")
    text: str = Field(min_length=1)
    type: ObsType
    confidence: Confidence


class ImageAnalysis(BaseModel):
    category: Category
    category_confidence: Confidence
    observations: list[Observation] = Field(default_factory=list)
    risks_visible: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    clarifying_question: str | None = None
    privacy_flags: list[PrivacyFlag] = Field(default_factory=list)
    is_civic_issue: bool


class UserContext(BaseModel):
    """Only facts the user typed. Nothing here is ever inferred."""

    location_text: str | None = None
    ongoing: bool | None = None
    notes: str | None = None
    clarification_answer: str | None = None

    def provided_fields(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for name in ("location_text", "notes", "clarification_answer"):
            val = getattr(self, name)
            if val and val.strip():
                out[name] = val.strip()
        if self.ongoing is not None:
            out["ongoing"] = "yes" if self.ongoing else "no"
        return out


class ClaimSource(BaseModel):
    statement: str
    source: str  # "o<N>" observation id, or "user:<field>"


class ComplaintDraft(BaseModel):
    issue_category: Category
    description: str
    location: str | None = None
    observed_evidence: list[str] = Field(default_factory=list)
    public_impact: str = ""
    requested_action: str
    language: Language
    claim_sources: list[ClaimSource] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    is_draft: bool = True  # always a draft; never submitted anywhere
