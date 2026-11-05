# CivicLens Project State
Last updated: 2026-11-05
Submission status: unknown. Original deadline Nov 4 2026 8:00 PM IST has passed; user not yet asked whether extended.

## Decisions
- Streamlit + Gemini primary + labeled mock fallback; evidence-ledger concept (phase 1, assistant defaults; user opted out of questions). See docs/DECISIONS.md.

## Phase status
| Phase | Status | Verified? | Commit |
|---|---|---|---|
| 1 | In progress (awaiting spike run) | see log | pending |

## Files
- src/civiclens/config.py env loading; providers/{base,gemini,mock}.py provider abstraction
- scripts/spike.py AI spike; app.py Streamlit skeleton
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
- Streamlit skeleton: NOT RUN (UNVERIFIED).

## Known issues / limitations
- No API key in environment: real model call NOT VERIFIED.
- No sample images yet.

## Open questions
- Is submission still open?
- Add GEMINI_API_KEY and sample images.
