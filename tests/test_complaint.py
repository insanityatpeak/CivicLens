"""Pipeline-logic tests for stage 2 (scripted provider; not model quality)."""
import json

import pytest

from civiclens.complaint import ComplaintError, generate_complaint
from civiclens.i18n import validate_language
from civiclens.schemas import ImageAnalysis
from conftest import ScriptedProvider, analysis_json, good_draft


def test_clean_draft_passes_first_try(analysis, ctx):
    p = ScriptedProvider([json.dumps(good_draft())])
    r = generate_complaint(p, analysis, ctx, "en")
    assert r.report.passed and not r.regenerated and r.draft.is_draft and p.calls == 1


def test_violation_triggers_one_regeneration_with_violations_listed(analysis, ctx):
    bad = good_draft(requested_action="Call 98765 43210 now.")
    p = ScriptedProvider([json.dumps(bad), json.dumps(good_draft())])
    r = generate_complaint(p, analysis, ctx, "en")
    assert r.regenerated and r.report.passed and p.calls == 2
    assert "invented_phone" in p.prompts[1]


def test_persistent_violation_returns_warnings_not_silence(analysis, ctx):
    bad = json.dumps(good_draft(requested_action="Call 98765 43210 now."))
    r = generate_complaint(ScriptedProvider([bad]), analysis, ctx, "en")
    assert not r.report.passed and r.warnings and r.regenerated


def test_malformed_output_twice_raises(analysis, ctx):
    with pytest.raises(ComplaintError) as e:
        generate_complaint(ScriptedProvider(["nope"]), analysis, ctx, "en")
    assert e.value.kind == "malformed_output"


def test_no_issue_refuses_to_draft(ctx):
    a = ImageAnalysis.model_validate_json(analysis_json(is_civic_issue=False, category="no_civic_issue"))
    with pytest.raises(ComplaintError) as e:
        generate_complaint(ScriptedProvider(["{}"]), a, ctx, "en")
    assert e.value.kind == "no_issue"


def test_unclear_without_answer_requires_clarification(ctx):
    a = ImageAnalysis.model_validate_json(analysis_json(category="unclear", category_confidence="low", clarifying_question="What is it?"))
    with pytest.raises(ComplaintError) as e:
        generate_complaint(ScriptedProvider(["{}"]), a, ctx.model_copy(update={"clarification_answer": None}), "en")
    assert e.value.kind == "needs_clarification"


def test_unsupported_language_rejected(analysis, ctx):
    with pytest.raises(ValueError):
        generate_complaint(ScriptedProvider(["{}"]), analysis, ctx, "fr")
    with pytest.raises(ValueError):
        validate_language("xx")


def test_prompt_contains_only_user_provided_facts(analysis):
    from civiclens.schemas import UserContext
    p = ScriptedProvider([json.dumps(good_draft(location=None, claim_sources=good_draft()["claim_sources"][:2]))])
    generate_complaint(p, analysis, UserContext(), "en")
    assert "location_text" not in p.prompts[0].split("User facts (JSON):")[1]
