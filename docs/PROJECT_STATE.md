# CivicLens Project State
Last updated: 2026-11-05
Submission status: unknown. Original deadline Nov 4 2026 8:00 PM IST has passed; user not yet asked whether extended.

## Decisions
- Streamlit + Gemini primary + labeled mock fallback; evidence-ledger concept (phase 1, assistant defaults; user opted out of questions). See docs/DECISIONS.md.

## Phase status
| Phase | Status | Verified? | Commit |
|---|---|---|---|
| 1 | Done except real-model spike | partial | 23467a0 |
| 2 | Code + unit tests done; real-model behaviour unverified | logic only | 0206a6d |
| 3 | UI built; flow tested headless with labeled fallback; visuals unseen | flow only | ab443d0 |
| 4 | Eval harness + hardening done; NO real metrics (no key, no images) | harness/tests only | pending |

## Files
- src/civiclens/config.py env loading; providers/{base,gemini,mock}.py provider abstraction
- scripts/spike.py AI spike; app.py Streamlit skeleton
- src/civiclens/{schemas,analysis,complaint,safety,i18n,parsing}.py: Phase 2 pipeline; tests/ (33 tests); scripts/run_pipeline.py
- app.py UI; src/civiclens/{ui_theme,export}.py; .streamlit/config.toml; providers/mock.py = labeled canned fallback with 3 scenarios
- eval/run_eval.py, eval/dataset.csv (header only), eval/REPORT.md (states no eval run), src/civiclens/evalmetrics.py, tests/test_eval.py; requirements-dev.txt
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
- Auto-blurring of faces/plates: NOT IMPLEMENTED (future work); privacy_flags reporting implemented, UI warning is Phase 3.

## Known issues / limitations
- No API key in environment: real model call NOT VERIFIED.
- No sample images yet.

## Open questions
- Is submission still open?
- Add GEMINI_API_KEY and sample images.
