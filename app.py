"""CivicLens UI: upload -> analysis (evidence ledger) -> [question] -> context -> editable draft."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from civiclens import ui_theme as ui
from civiclens.analysis import AnalysisError, analyze_image
from civiclens.complaint import ComplaintError, generate_complaint
from civiclens.config import ConfigError
from civiclens.export import draft_to_text, text_to_markdown, to_txt_bytes
from civiclens.i18n import CATEGORY_LABELS, SUPPORTED
from civiclens.providers import get_provider
from civiclens.providers.mock import SCENARIOS, MockProvider
from civiclens.schemas import UserContext

st.set_page_config(page_title="CivicLens", page_icon="🔎", layout="centered")
st.markdown(ui.CSS, unsafe_allow_html=True)

DEFAULTS = {"stage": "upload", "img": None, "analysis": None, "answer": None, "complaint": None,
            "error": None, "use_mock": False, "scenario": "pothole", "ctx": None, "lang": "en", "runs": 0}
MAX_RUNS_PER_SESSION = 10  # soft per-session cap to limit quota abuse on a shared key (not a global rate limit)
for _k, _v in DEFAULTS.items():
    st.session_state.setdefault(_k, _v)
S = st.session_state


def start_over() -> None:
    keep = {"use_mock": S.use_mock, "scenario": S.scenario, "runs": S.runs}
    S.clear()
    S.update(DEFAULTS | keep)


def html(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


# ---------- header ----------
html('<div class="brand"><b>CivicLens</b><span>See a problem. Report a solution.</span></div>')

# ---------- provider ----------
if S.use_mock:
    provider = MockProvider(S.scenario)
else:
    try:
        provider = get_provider()
    except (ConfigError, ValueError) as exc:
        st.error(f"{exc}")
        st.caption("You can still try the flow with canned demonstration output. It is not real AI.")
        if st.button("Use demonstration fallback"):
            S.use_mock = True
            st.rerun()
        st.stop()

if provider.is_fallback:
    html(ui.notice("fallback", "DEMONSTRATION FALLBACK: results below are canned examples, not real AI analysis of your photo."))
    if S.stage == "upload":
        S.scenario = st.selectbox("Demo scenario to play", SCENARIOS, index=SCENARIOS.index(S.scenario))
        provider = MockProvider(S.scenario)

with st.expander("How it works"):
    st.write(
        "1. **AI looks at your photo** and lists what it can see, marking each item as *seen in the photo* or *assumed*.\n"
        "2. **If it is unsure**, it asks you one short question instead of guessing.\n"
        "3. **AI writes a draft** using only that list and the details you type.\n"
        "4. **Rule-based checks** (not AI) flag invented phone numbers, dates, departments or locations before you see the draft."
    )

if S.error:
    st.error(S.error)

# ---------- stage: upload ----------
if S.stage == "upload":
    up = st.file_uploader("Photo of the problem", type=["jpg", "jpeg", "png", "webp"], help="Up to 10 MB")
    if up is not None:
        S.img = up.getvalue()
    if S.img:
        st.image(S.img, width="stretch")
        limited = not provider.is_fallback and S.runs >= MAX_RUNS_PER_SESSION
        if limited:
            st.warning(f"This session has used its {MAX_RUNS_PER_SESSION} photo analyses. Please reload the page later to continue.")
        if st.button("Analyze photo", type="primary", disabled=limited):
            S.error = None
            S.runs += 1
            with st.status("Reading your photo...", expanded=True) as status:
                try:
                    st.write("Checking the image")
                    res = analyze_image(provider, S.img)
                    st.write("Separating what is visible from what is assumed")
                    status.update(label="Analysis ready", state="complete")
                except AnalysisError as exc:
                    status.update(label="Could not analyze this photo", state="error")
                    S.error = exc.message
                    st.rerun()
            S.analysis, S.stage = res, "analysis"
            st.rerun()

# ---------- stage: analysis ----------
elif S.stage == "analysis":
    res = S.analysis
    a = res.analysis
    st.image(S.img, width=240)
    if a.privacy_flags:
        html(ui.notice("warn", ui.PRIVACY_NOTE))

    label = CATEGORY_LABELS["en"][a.category]
    st.subheader(label)
    if not a.is_civic_issue:
        st.info("We did not find a civic issue in this photo, so there is nothing to report.")
        st.button("Try another photo", on_click=start_over, type="primary")
        st.stop()

    st.caption(f"We are {ui.CONF_WORDS[a.category_confidence]} about this category.")
    st.markdown("**Evidence ledger**: what the AI saw versus what it assumed")
    html('<div class="card">' + "".join(ui.observation_row(o.text, o.type, o.confidence) for o in a.observations) + "</div>")

    if a.clarifying_question and not S.answer:
        st.markdown("**One quick question**")
        with st.form("clarify"):
            ans = st.text_input(a.clarifying_question)
            go = st.form_submit_button("Continue", type="primary")
        if go:
            if ans.strip():
                S.answer = ans.strip()
                st.rerun()
            st.warning("Please type a short answer, or choose a different photo.")
        st.button("Use a different photo", on_click=start_over)
        st.stop()

    st.markdown("**Add details so someone can act on this**")
    with st.form("context"):
        loc = st.text_input("Where is it? (street, landmark, area)")
        ongoing = st.radio("Is it still there?", ["Not sure", "Yes, ongoing", "No, it is fixed"], horizontal=True)
        notes = st.text_area("Anything else? (optional)")
        lang = st.radio("Complaint language", list(SUPPORTED), format_func=SUPPORTED.get, horizontal=True)
        go = st.form_submit_button("Create complaint draft", type="primary")
    if not loc.strip():
        st.caption("Tip: adding a landmark makes this much easier to act on.")
    if go:
        ctx = UserContext(
            location_text=loc.strip() or None,
            ongoing={"Yes, ongoing": True, "No, it is fixed": False}.get(ongoing),
            notes=notes.strip() or None,
            clarification_answer=S.answer,
        )
        with st.status("Writing your draft...", expanded=True) as status:
            try:
                st.write("Writing from the evidence ledger and your details")
                cr = generate_complaint(provider, a, ctx, lang)
                st.write("Checking every statement against its source")
                status.update(label="Draft ready", state="complete")
            except ComplaintError as exc:
                status.update(label="Could not write the draft", state="error")
                S.error = exc.message
                st.rerun()
        S.complaint, S.ctx, S.lang, S.stage = cr, ctx, lang, "draft"
        S.edited_text = draft_to_text(cr.draft)
        S.error = None
        st.rerun()
    st.button("Start over", on_click=start_over)

# ---------- stage: draft ----------
elif S.stage == "draft":
    cr, a, ctx = S.complaint, S.analysis.analysis, S.ctx
    html(ui.notice("info", "This is a DRAFT for you to review. Nothing has been submitted anywhere."))
    if not cr.report.passed:
        html(ui.notice("warn", "Some statements could not be fully checked. Please read carefully before using this draft:"))
        for m in cr.warnings:
            st.markdown(f"- {m}")

    st.markdown("**Your draft** (edit freely)")
    text = st.text_area("Complaint text", key="edited_text", height=320, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    c1.download_button("Download .txt", to_txt_bytes(text), "complaint_draft.txt", "text/plain; charset=utf-8", width="stretch")
    c2.download_button("Download .md", text_to_markdown(text).encode("utf-8"), "complaint_draft.md", "text/markdown; charset=utf-8", width="stretch")
    with st.expander("Copy text"):
        st.code(text, language=None)

    st.markdown("**Where each statement comes from**")
    rows = []
    obs = {o.id: o for o in a.observations}
    for c in cr.draft.claim_sources:
        if c.source.startswith("user:"):
            rows.append(ui.source_row(c.statement, "You told us", "user"))
        elif c.source in obs and obs[c.source].type == "observed":
            rows.append(ui.source_row(c.statement, "Seen in photo", "seen"))
        else:
            rows.append(ui.source_row(c.statement, "Assumed", "assumed"))
    html('<div class="card"><table class="src">' + "".join(rows) + "</table></div>")
    if cr.draft.missing_info:
        st.caption("Still missing: " + ", ".join(cr.draft.missing_info))

    st.markdown("**Where to send this**")
    html(ui.notice("info", ui.WHERE_TO_SEND))
    st.caption(ui.DISCLAIMER)

    b1, b2 = st.columns(2)
    if b1.button("Edit details", width="stretch"):
        S.stage = "analysis"
        S.complaint = None
        st.rerun()
    b2.button("Start over", on_click=start_over, width="stretch")
