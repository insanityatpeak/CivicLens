# CivicLens Project State
Last updated: 2026-11-05
Submission status: unknown. Original deadline Nov 4 2026 8:00 PM IST has passed; user not yet asked whether extended.

## Decisions
- FastAPI + static SPA frontend (replaced Streamlit, user choice, see docs/UI_DESIGN.md) + Gemini primary + labeled mock fallback; evidence-ledger concept (phase 1, assistant defaults; user opted out of questions). See docs/DECISIONS.md.

## Phase status
| Phase | Status | Verified? | Commit |
|---|---|---|---|
| 1 | Done except real-model spike | partial | 23467a0 |
| 2 | Code + unit tests done; real-model behaviour unverified | logic only | 0206a6d |
| 3 | UI built; flow tested headless with labeled fallback; visuals unseen | flow only | ab443d0 |
| 4 | Eval harness + hardening done; NO real metrics (no key, no images) | harness/tests only | 1486e93 |
| 5 | README, DEPLOY.md, checklist, session cap done; NOT DEPLOYED; no screenshots | docs + tests + fresh clone | a4d1f5e |

## Files
- GitHub: https://github.com/insanityatpeak/CivicLens (public, main)
- src/civiclens/config.py env loading; providers/{base,gemini,mock}.py provider abstraction
- scripts/spike.py AI spike
- src/civiclens/{schemas,analysis,complaint,safety,i18n,parsing}.py: Phase 2 pipeline; tests/ (33 tests); scripts/run_pipeline.py
- src/civiclens/web/{server.py,static/{index.html,app.css,app.js,i18n.js}} UI + API; src/civiclens/export.py; providers/mock.py = labeled canned fallback with 3 scenarios
- eval/run_eval.py, eval/dataset.csv (header only), eval/REPORT.md (states no eval run), src/civiclens/evalmetrics.py, tests/test_eval.py; requirements-dev.txt
- docs/DECISIONS.md, docs/plans/phase-1-plan.md, data/SOURCES.md

## How to run
```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # add GEMINI_API_KEY
python scripts/spike.py [data/samples/pothole.jpg]
uvicorn civiclens.web.server:app --app-dir src --port 8000
```

## Verification log
- `pip install -r requirements.txt` in fresh .venv -> imports of google.genai, streamlit, pydantic, PIL OK (VERIFIED)
- `python scripts/spike.py` (no key) -> clear CONFIG ERROR, exit 2 (VERIFIED)
- `CIVICLENS_PROVIDER=mock python scripts/spike.py` -> labeled fallback banner, canned text, exit 0 (VERIFIED; harness only, not AI)
- Real Gemini TEXT call: VERIFIED 2026-11-05 after user added key: `python scripts/spike.py` -> model=gemini-2.5-flash, fallback=False, latency 11.4s then 7.6s, ~200-260 output tokens. Hindi reply was fluent and polite (reviewer: assistant, not a human rater). It added unrequested transliteration/translation, so free text from the model must not be used raw; JSON-only prompts are required (they are).
- Real Gemini IMAGE (vision) call: NOT VERIFIED (no sample images yet).
- Streamlit skeleton: served HTTP 200 on :8501 with mock provider; page not viewed in a browser (UI UNVERIFIED).
- `.venv/Scripts/python -m pytest -q` -> `33 passed in 0.71s` (VERIFIED; scripted fake provider, tests pipeline logic NOT model quality)
- Validator catches injected phone, date, department, unknown source, invented location, unhedged inference, submission claim (VERIFIED in unit tests)
- `python scripts/run_pipeline.py img.jpg` no key -> CONFIG ERROR exit 2; with mock -> clean ANALYSIS ERROR malformed_output exit 1, no stack trace (VERIFIED)
- Real-model analysis/complaint runs on sample images: NOT RUN (no key, no sample images). Prompts and EN-vs-HI direct generation quality UNVERIFIED.
- `.venv/Scripts/python -m pytest -q` -> `44 passed in 4.27s` (VERIFIED). Includes Streamlit AppTest flows: pothole EN+HI to draft, no-issue declined, unclear asks question first, fallback banner always shown. All use the demonstration fallback, so they test UI/pipeline logic, NOT real AI.
- Hindi export: UTF-8 with BOM round-trip tested (VERIFIED in unit test); rendering in a real browser/Notepad NOT VIEWED.
- Visual look (fonts, colors, mobile layout, contrast in practice): UNVERIFIED, no browser screenshot taken. docs/screenshots/ intentionally empty.
- Sample-image buttons: NOT IMPLEMENTED (no licensed images). Streamlit server was stopped at user request.
- `.venv/Scripts/ruff check . --exclude .venv` -> `All checks passed!` after fixing 40 findings (unused imports, import order; one TRY004 kept as ValueError by design) (VERIFIED)
- `.venv/Scripts/python -m pytest -q` -> `50 passed in 4.51s` (VERIFIED; includes harness tests on generated images + fallback: harness mechanics ONLY)
- Fresh venv (scratchpad/freshvenv) `pip install -r requirements.txt -r requirements-dev.txt` then `pytest` -> `50 passed in 6.70s`; `pip check` -> `No broken requirements found.` (VERIFIED)
- Secret scan (regexes for Google/OpenAI/Anthropic/GitHub/AWS keys, private keys, key=... literals) over working tree and `git log -p --all` -> no matches; no .env or .venv tracked (VERIFIED)
- Code review greps for key printing, TODO/FIXME, debugger calls -> none (VERIFIED)
- `python eval/run_eval.py` with empty dataset -> exits 3 with "nothing was evaluated" (VERIFIED in test). Real evaluation: NOT RUN. No model metrics exist. Hindi rubric and unsupported-claim spot-check: PENDING (rating_sheet.csv generated per run, to be filled by user).
- Phase 4 step 4 (targeted fix after eval): NOT DONE, blocked on a real eval run.
- Real-model stage-2 smoke test (SYNTHETIC hand-written pothole ledger, not model-read photos; N=3 runs, NOT an evaluation): EN with location, HI with location, EN without location -> all 3 `validator_passed=True`, `regenerated=False`, latency 7.8-8.9s, no invented location/date/department/phone; no-location draft set location null and listed it in missing_info (VERIFIED, observed output). Quirks seen: EN draft hedged a user-stated fact ("appears to be ongoing"); HI claim table entry for ongoing had statement "yes" (shows oddly in the UI source table; not yet fixed); HI draft kept the user's English location verbatim (expected).
- Console fix: scripts printed Hindi -> UnicodeEncodeError on Windows cp1252; scripts/spike.py, run_pipeline.py, eval/run_eval.py now force UTF-8 stdout (VERIFIED by rerun).
- Phase 5: `pytest -q` -> `52 passed in 7.43s` (VERIFIED; adds tests that a real-provider session is capped at 10 analyses via dummy key, and that fallback sessions are not capped). ruff clean.
- Phase 6 (2026-11-05): real runs on 4 photos earlier today: garbage dumping (faces flagged, EN draft passed validator), litter by wall (EN draft passed), crowded train (classified other_civic_issue; EN draft about overcrowding passed validator; over-acceptance concern), pothole.jpg (analysis OK; draft hit 503). Then `429 RESOURCE_EXHAUSTED`: Gemini free tier limit 20 requests/day for gemini-2.5-flash exhausted; ~17.5h to reset. Rehearsal of Hindi-from-photo and pothole draft therefore NOT DONE.
- After user supplied a new GEMINI_API_KEY: still `429 RESOURCE_EXHAUSTED` on gemini-2.5-flash (free-tier quota is per Google project per model, so a key from the same project shares it). `gemini-2.5-flash-lite` -> 404 "no longer available to new users, use gemini-3.5-flash-lite"; `gemini-3.5-flash-lite` -> 503 high demand (one attempt). Pothole draft and Hindi-from-photo rehearsal remain NOT DONE. Options: key from a NEW Google project, paid tier, wait ~17h, or retry gemini-3.5-flash-lite later (model default in .env.example is unchanged and untested on 3.5).
- Demo script timing by word count: 191 words = ~76-88 s at 130-150 wpm; 30 s version 66 words = ~26-30 s (computed by script, not read aloud).
- Another session is rebuilding the UI (src/civiclens/web/, tests/test_web.py, staged deletion of tests/test_app_flow.py). Not touched or committed by this session. Working-tree `pytest` today: 58 passed (includes that session's tests); committed main: 52.
- Auto-blurring of faces/plates: NOT IMPLEMENTED (future work); privacy_flags reporting implemented, UI warning is Phase 3.

## Known issues / limitations
- Key now provided via .env (git-ignored, not tracked). Vision path and sample images still outstanding.
- No sample images yet.

## Open questions
- Is submission still open?
- Add GEMINI_API_KEY and sample images.
