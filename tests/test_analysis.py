"""Pipeline-logic tests for stage 1 (scripted provider; not model quality)."""
import io

import pytest
from conftest import ScriptedProvider, analysis_json, jpeg_bytes
from PIL import Image

from civiclens.analysis import AnalysisError, analyze_image, prepare_image
from civiclens.parsing import extract_json


def test_extract_json_handles_fences_and_prose():
    assert extract_json('Here:\n```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('noise {"a": 2} tail') == {"a": 2}
    with pytest.raises(ValueError):
        extract_json("no json here")


def test_valid_analysis_parses():
    r = analyze_image(ScriptedProvider([analysis_json()]), jpeg_bytes())
    assert r.analysis.category == "pothole_road_damage" and len(r.analysis.observations) == 2


def test_malformed_then_valid_retries_once():
    p = ScriptedProvider(["not json", analysis_json()])
    assert analyze_image(p, jpeg_bytes()).analysis.is_civic_issue
    assert p.calls == 2


def test_malformed_twice_raises_typed_error():
    with pytest.raises(AnalysisError) as e:
        analyze_image(ScriptedProvider(["bad"]), jpeg_bytes())
    assert e.value.kind == "malformed_output"


def test_schema_violation_counts_as_malformed():
    with pytest.raises(AnalysisError):
        analyze_image(ScriptedProvider([analysis_json(category="made_up")]), jpeg_bytes())


def test_non_civic_forced_to_no_issue_without_question():
    r = analyze_image(ScriptedProvider([analysis_json(is_civic_issue=False, category="pothole_road_damage", clarifying_question="x?")]), jpeg_bytes())
    assert r.analysis.category == "no_civic_issue" and r.analysis.clarifying_question is None


def test_unclear_gets_clarifying_question_even_if_model_omits_it():
    r = analyze_image(ScriptedProvider([analysis_json(category="unclear", category_confidence="low")]), jpeg_bytes())
    assert r.analysis.clarifying_question


def test_low_confidence_keeps_models_own_question():
    r = analyze_image(ScriptedProvider([analysis_json(category_confidence="low", clarifying_question="Is that water or oil?")]), jpeg_bytes())
    assert r.analysis.clarifying_question == "Is that water or oil?"


def test_rejects_non_image_empty_and_oversize():
    with pytest.raises(AnalysisError) as e:
        prepare_image(b"hello world")
    assert e.value.kind == "invalid_image"
    with pytest.raises(AnalysisError):
        prepare_image(b"")
    with pytest.raises(AnalysisError) as e:
        prepare_image(b"0" * (10 * 1024 * 1024 + 1))
    assert e.value.kind == "too_large"


def test_rejects_unsupported_format():
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, format="BMP")
    with pytest.raises(AnalysisError) as e:
        prepare_image(buf.getvalue())
    assert e.value.kind == "unsupported_type"


def test_prepare_downsizes_and_strips_exif():
    out = prepare_image(jpeg_bytes((4000, 3000)))
    img = Image.open(io.BytesIO(out))
    assert max(img.size) <= 1568 and not img.getexif()
