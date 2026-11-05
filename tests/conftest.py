"""Shared fixtures. ScriptedProvider replays canned replies: it tests pipeline LOGIC, not model quality."""
from __future__ import annotations

import io
import json

import pytest
from PIL import Image

from civiclens.providers.base import ModelProvider, ProviderResult
from civiclens.schemas import ImageAnalysis, Observation, UserContext


class ScriptedProvider(ModelProvider):
    name = "scripted"

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls = 0
        self.prompts: list[str] = []

    def generate(self, prompt, image_bytes=None, mime_type="image/jpeg"):
        self.prompts.append(prompt)
        self.calls += 1
        text = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return ProviderResult(text=text, model="scripted", latency_s=0.01)


def jpeg_bytes(size=(64, 48)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 120, 120)).save(buf, format="JPEG")
    return buf.getvalue()


def analysis_json(**over) -> str:
    base = {
        "category": "pothole_road_damage",
        "category_confidence": "high",
        "observations": [
            {"id": "o1", "text": "A hole in the road surface", "type": "observed", "confidence": "high"},
            {"id": "o2", "text": "Vehicles may swerve around it", "type": "inferred", "confidence": "medium"},
        ],
        "risks_visible": [],
        "missing_info": ["location"],
        "clarifying_question": None,
        "privacy_flags": [],
        "is_civic_issue": True,
    }
    base.update(over)
    return json.dumps(base)


@pytest.fixture
def analysis() -> ImageAnalysis:
    return ImageAnalysis.model_validate_json(analysis_json())


@pytest.fixture
def ctx() -> UserContext:
    return UserContext(location_text="Near the bus stop on Main Road", ongoing=True)


def good_draft(**over) -> dict:
    d = {
        "description": "There is a hole in the road surface near the bus stop on Main Road.",
        "location": "Near the bus stop on Main Road",
        "observed_evidence": ["A hole in the road surface"],
        "public_impact": "Vehicles may swerve around it, which could be unsafe.",
        "requested_action": "Please inspect and repair the road.",
        "claim_sources": [
            {"statement": "A hole in the road surface", "source": "o1"},
            {"statement": "Vehicles may swerve around it, which could be unsafe.", "source": "o2"},
            {"statement": "Near the bus stop on Main Road", "source": "user:location_text"},
        ],
        "missing_info": [],
    }
    d.update(over)
    return d
