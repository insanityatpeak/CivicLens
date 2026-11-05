"""Headless Streamlit AppTest of the UI flow using the labeled demonstration fallback (logic, not looks)."""
from pathlib import Path

from conftest import jpeg_bytes
from streamlit.testing.v1 import AppTest


def fresh(scenario="pothole") -> AppTest:
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30)
    at.session_state["use_mock"] = True
    at.session_state["scenario"] = scenario
    at.session_state["img"] = jpeg_bytes()
    return at.run()


def click(at, label):
    next(b for b in at.button if b.label == label).click()
    return at.run()


def texts(at):
    return " ".join(m.value for m in at.markdown) + " ".join(e.value for e in at.error) + " ".join(i.value for i in at.info)


def test_fallback_banner_always_shown():
    assert "DEMONSTRATION FALLBACK" in texts(fresh())


def test_pothole_flow_to_draft_in_english_and_hindi():
    for lang_idx, needle in ((0, "COMPLAINT DRAFT"), (1, "शिकायत")):
        at = click(fresh(), "Analyze photo")
        assert "Seen in photo" in texts(at) and "Assumed" in texts(at)
        at.radio[1].set_value(("en", "hi")[lang_idx])
        at = click(at, "Create complaint draft") if any(b.label == "Create complaint draft" for b in at.button) else at.run()
        assert not at.exception
        assert needle in at.text_area[0].value
        assert "Nothing has been submitted" in texts(at)


def test_no_issue_scenario_declines():
    at = click(fresh("no_issue"), "Analyze photo")
    assert "nothing to report" in texts(at)
    assert not any(b.label == "Create complaint draft" for b in at.button)


def test_unclear_scenario_asks_question_first():
    at = click(fresh("unclear"), "Analyze photo")
    assert any("water, oil" in t.label for t in at.text_input)
    assert not any(b.label == "Create complaint draft" for b in at.button)
