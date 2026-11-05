# CivicLens Project State
Last updated: 2026-11-05
Submission status: unknown. Original deadline Nov 4 2026 8:00 PM IST has passed; user not yet asked whether extended.

## Decisions
- Streamlit + Gemini primary + labeled mock fallback; evidence-ledger concept (phase 1, assistant defaults; user opted out of questions). See docs/DECISIONS.md.

## Phase status
| Phase | Status | Verified? | Commit |
|---|---|---|---|
| 1 | Done except real-model spike | partial | 23467a0 |
| 2 | Code + unit tests done; real-model behaviour unverified | logic only | pending |

## Files
- src/civiclens/config.py env loading; providers/{base,gemini,mock}.py provider abstraction
- scripts/spike.py AI spike; app.py Streamlit skeleton
- src/civiclens/{schemas,analysis,complaint,safety,i18n,parsing}.py: Phase 2 pipeline; tests/ (33 tests); scripts/run_pipeline.py
- docs/DECISIONS.md, docs/plans/phase-1-plan.md, data/SOURCES.md

## How to run
```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # add GEMINI_API_KEY
python scripts/spike.py [data/samples/pothole.jpg]
streamlit run app.py
```

## Verification log
- `pip install -r requirements.txt` in fresh .venv -> imports of google.genai, streamlit, pydantic, PIL OK (VERIFIED)
- `python scripts/spike.py` (no key) -> clear CONFIG ERROR, exit 2 (VERIFIED)
- `CIVICLENS_PROVIDER=mock python scripts/spike.py` -> labeled fallback banner, canned text, exit 0 (VERIFIED; harness only, not AI)
- Real Gemini call: NOT VERIFIED (no key). Hindi quality check: NOT VERIFIED.
- Streamlit skeleton: served HTTP 200 on :8501 with mock provider; page not viewed in a browser (UI UNVERIFIED).
- `.venv/Scripts/python -m pytest -q` -> `33 passed in 0.71s` (VERIFIED; scripted fake provider, tests pipeline logic NOT model quality)
- Validator catches injected phone, date, department, unknown source, invented location, unhedged inference, submission claim (VERIFIED in unit tests)
- `python scripts/run_pipeline.py img.jpg` no key -> CONFIG ERROR exit 2; with mock -> clean ANALYSIS ERROR malformed_output exit 1, no stack trace (VERIFIED)
- Real-model analysis/complaint runs on sample images: NOT RUN (no key, no sample images). Prompts and EN-vs-HI direct generation quality UNVERIFIED.
- Auto-blurring of faces/plates: NOT IMPLEMENTED (future work); privacy_flags reporting implemented, UI warning is Phase 3.

## Known issues / limitations
- No API key in environment: real model call NOT VERIFIED.
- No sample images yet.

## Open questions
- Is submission still open?
- Add GEMINI_API_KEY and sample images.
