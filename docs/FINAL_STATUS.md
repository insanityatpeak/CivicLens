# CivicLens Final Status

Date: 2026-11-05. Repo: https://github.com/insanityatpeak/CivicLens (public). Committed state described below is the Streamlit app at `main`. **A separate session is replacing/updating the UI (`src/civiclens/web/`, `tests/test_web.py`, a staged deletion of `tests/test_app_flow.py`); that work is uncommitted and NOT covered by this report.**

## Features
**Implemented and verified** (run and seen)
- Image validation, resize, EXIF strip (unit tests).
- Stage-1 analysis with JSON parse/retry and uncertainty policy: unit tests (scripted provider) plus real Gemini runs on 3 real photos (garbage dumping, litter, crowded train) and the pothole photo (analysis only).
- Stage-2 grounded draft EN/HI: real Gemini on a hand-written ledger (3 drafts, all validator-pass first try); real photos: 3 English drafts passed the validator.
- Rule-based validator catching injected phone, date, department, unknown source, invented location, unhedged inference, submission claim (unit tests).
- Faces privacy flag on a real photo (garbage-dumping photo).
- Eval harness mechanics (generated images + fallback, stamped HARNESS TEST ONLY).
- Fresh-clone install and tests; secret scan clean (tree and history).

**Implemented but unverified**
- Streamlit UI visuals, Hindi rendering in a browser, mobile layout (never viewed).
- Hindi draft from a real photo (only from a hand-written ledger).
- Clarifying question and no-issue decline on real photos (only in the labeled fallback and unit tests).
- Pothole draft on the real model (one 503, then quota exhausted).
- Per-session cap against a real key (tested with a dummy key only).

**Not implemented**
- Real evaluation/metrics; Hindi quality ratings; unsupported-claim spot-check.
- Face/plate blurring; official reporting-channel links; deployment; screenshots; LICENSE; bring-your-own-key; global rate limiting.

## AI models and keys
Google Gemini `gemini-2.5-flash` via `google-genai`, key from `GEMINI_API_KEY` in `.env` (git-ignored, never committed). Temperature 0.2. Labeled canned `MockProvider` as a demonstration fallback. **Free tier observed limit: 20 requests/day for this model; exhausted on 2026-11-05 (resets in ~17.5 h).**

## Files (committed)
```
app.py                       Streamlit UI (being superseded in another session)
src/civiclens/               config, providers/{base,gemini,mock}, schemas, analysis,
                             complaint, safety (validator), i18n, parsing, export,
                             ui_theme, evalmetrics
scripts/                     spike.py, run_pipeline.py
eval/                        run_eval.py, dataset.csv (empty), REPORT.md (no eval run)
tests/                       analysis, safety, complaint, mock/export, eval, app flow
data/SOURCES.md              image sources (CC0 samples recorded by another session)
```

## Tests
- Committed `main` (Phase 5 state): `52 passed` (recorded earlier). Ruff clean.
- Current working tree today: `58 passed, 1 warning` and ruff clean, but that includes the other session's uncommitted `tests/test_web.py` and excludes its staged deletion, so treat 52 as the committed number.
- All tests use scripted/canned providers: they test logic, not model quality.

## Evaluation
None. `eval/REPORT.md` says so. Smoke tests only (N=3 drafts from a synthetic ledger; 3 real photos; no labels).

## Run locally
`pip install -r requirements.txt`, set `GEMINI_API_KEY` in `.env`, `streamlit run app.py` (committed UI). CLI: `python scripts/run_pipeline.py photo.jpg --lang hi`. The other session's new UI may change this command.

## Deployment
NOT DEPLOYED. `docs/DEPLOY.md` has steps. Note the free-tier quota above makes a shared public key impractical.

## Known limitations
Vision stage unevaluated; crowded-train photo was drafted as an "other civic issue" about overcrowding (over-acceptance risk); validator is pattern-based; English/Hindi only; no blurring; quota.

## Remaining user actions
