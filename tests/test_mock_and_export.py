"""Tests of the labeled demonstration fallback and export (pipeline logic, not model quality)."""
import pytest

from civiclens.analysis import analyze_image
from civiclens.complaint import generate_complaint
from civiclens.export import draft_to_text, to_txt_bytes
from civiclens.providers.mock import MockProvider
from civiclens.schemas import UserContext
from conftest import jpeg_bytes


def run(scenario, lang="en", **ctx):
    p = MockProvider(scenario)
    a = analyze_image(p, jpeg_bytes()).analysis
    return a, generate_complaint(p, a, UserContext(**ctx), lang)


@pytest.mark.parametrize("lang", ["en", "hi"])
def test_mock_pothole_draft_passes_validator(lang):
    _, r = run("pothole", lang, location_text="Near the bus stop", ongoing=True)
    assert r.report.passed, r.warnings
    assert r.is_fallback and r.draft.is_draft


def test_mock_without_location_does_not_invent_one():
    _, r = run("pothole")
    assert r.draft.location is None and "location" in r.draft.missing_info


def test_mock_unclear_asks_question_and_drafts_after_answer():
    p = MockProvider("unclear")
    a = analyze_image(p, jpeg_bytes()).analysis
    assert a.clarifying_question
    r = generate_complaint(p, a, UserContext(clarification_answer="It is dirty water"), "en")
    assert r.draft.issue_category == "unclear"


def test_mock_no_issue_is_declined():
    a, _ = None, None
    a = analyze_image(MockProvider("no_issue"), jpeg_bytes()).analysis
    assert not a.is_civic_issue and a.category == "no_civic_issue"


def test_hindi_export_roundtrips_in_utf8_with_bom():
    _, r = run("pothole", "hi", location_text="Main Road")
    text = draft_to_text(r.draft)
    raw = to_txt_bytes(text)
    assert raw.startswith(b"\xef\xbb\xbf") and raw.decode("utf-8-sig") == text
    assert "शिकायत" in text and "�" not in text


def test_export_states_not_submitted():
    _, r = run("pothole")
    assert "not submitted" in draft_to_text(r.draft)
