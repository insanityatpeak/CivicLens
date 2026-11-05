"""Pipeline-logic tests for the grounding validator."""

from conftest import good_draft

from civiclens.safety import validate_draft
from civiclens.schemas import ComplaintDraft, UserContext


def make(analysis, **over) -> ComplaintDraft:
    return ComplaintDraft.model_validate({**good_draft(**over), "issue_category": analysis.category, "language": "en"})


def codes(report):
    return {i.code for i in report.issues}


def test_good_draft_passes(analysis, ctx):
    assert validate_draft(make(analysis), analysis, ctx, "en").passed


def test_injected_phone_number_is_caught(analysis, ctx):
    d = make(analysis, description="Hole near bus stop. Call 98765 43210 for details.")
    assert "invented_phone" in codes(validate_draft(d, analysis, ctx))


def test_injected_date_is_caught(analysis, ctx):
    d = make(analysis, public_impact="This has been like this since 12/03/2024.")
    assert "invented_date" in codes(validate_draft(d, analysis, ctx))


def test_injected_department_is_caught(analysis, ctx):
    d = make(analysis, requested_action="Please ask the Municipal Corporation to repair it.")
    assert "invented_authority" in codes(validate_draft(d, analysis, ctx))


def test_authority_allowed_if_user_typed_it(analysis):
    ctx = UserContext(location_text="Main Road", notes="Reported before to the PWD")
    d = make(analysis, location="Main Road", requested_action="Please forward to the PWD.",
             claim_sources=good_draft()["claim_sources"][:2] + [{"statement": "Main Road", "source": "user:location_text"}])
    assert "invented_authority" not in codes(validate_draft(d, analysis, ctx))


def test_unknown_source_id_is_caught(analysis, ctx):
    d = make(analysis, claim_sources=[{"statement": "A hole in the road surface", "source": "o9"}])
    assert "bad_source" in codes(validate_draft(d, analysis, ctx))


def test_user_source_for_field_not_provided_is_caught(analysis):
    ctx = UserContext()  # user gave nothing
    d = make(analysis, location=None, claim_sources=[{"statement": "A hole in the road surface", "source": "user:notes"}])
    assert "bad_source" in codes(validate_draft(d, analysis, ctx))


def test_invented_location_is_caught(analysis):
    d = make(analysis)  # has location but user gave none
    assert "invented_location" in codes(validate_draft(d, analysis, UserContext()))


def test_unhedged_inference_is_caught(analysis, ctx):
    d = make(analysis, claim_sources=[{"statement": "The road is dangerous.", "source": "o2"},
                                      {"statement": "A hole in the road surface", "source": "o1"}])
    assert "unhedged_inference" in codes(validate_draft(d, analysis, ctx))


def test_evidence_without_source_is_caught(analysis, ctx):
    d = make(analysis, observed_evidence=["A hole in the road surface", "The hole is two metres wide"])
    assert "unmapped_evidence" in codes(validate_draft(d, analysis, ctx))


def test_submission_claim_is_caught(analysis, ctx):
    d = make(analysis, description="This complaint has been submitted to the authorities.")
    assert "claims_submission" in codes(validate_draft(d, analysis, ctx))


def test_hindi_language_mismatch_is_caught(analysis, ctx):
    d = make(analysis)  # English text, language field en
    assert "wrong_language" in codes(validate_draft(d, analysis, ctx, "hi"))


def hindi(d):
    """Translate every model-written part of the draft, keeping the ledger-linked claims aligned."""
    hi = "सड़क पर एक बड़ा गड्ढा है।"
    claims = [c.model_copy(update={"statement": hi}) if not c.source.startswith("user:") else c for c in d.claim_sources]
    return d.model_copy(update={"language": "hi", "description": hi, "public_impact": hi, "requested_action": hi,
                                "observed_evidence": [hi for _ in d.observed_evidence], "claim_sources": claims})


def test_hindi_draft_passes_language_check(analysis, ctx):
    assert "wrong_language" not in codes(validate_draft(hindi(make(analysis)), analysis, ctx, "hi"))


def test_hindi_draft_with_english_evidence_bullets_is_caught(analysis, ctx):
    d = hindi(make(analysis)).model_copy(update={"observed_evidence": ["A hole in the road surface"]})
    report = validate_draft(d, analysis, ctx, "hi")
    assert any(i.code == "wrong_language" and "observed_evidence" in i.where for i in report.issues)


def test_user_typed_location_is_exempt_from_hindi_check(analysis, ctx):
    d = hindi(make(analysis)).model_copy(update={"location": "Near Church Street junction"})
    assert not any(i.code == "wrong_language" and "location" in i.where for i in validate_draft(d, analysis, ctx, "hi").issues)


def test_english_word_left_in_hindi_text_is_caught(analysis, ctx):
    d = hindi(make(analysis))
    d = d.model_copy(update={"description": "सड़क पर कंक्रीट की रोकथाम दीवार (retaining wall) के पास गड्ढा है।"})
    report = validate_draft(d, analysis, ctx, "hi")
    assert any(i.code == "english_in_hindi" and "retaining" in i.message and i.where == "description" for i in report.issues)


def test_acronyms_and_user_typed_words_are_allowed_in_hindi(analysis):
    ctx = UserContext(location_text="Gali no. 4, Jangammet", ongoing=True)
    d = hindi(make(analysis, location="Gali no. 4, Jangammet"))
    d = d.model_copy(update={"description": "गली no. 4, Jangammet में कचरा है। कृपया BBMP या SMS से सूचित करें।"})
    codes_ = {i.code for i in validate_draft(d, analysis, ctx, "hi").issues}
    assert "english_in_hindi" not in codes_
