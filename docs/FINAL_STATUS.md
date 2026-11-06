# CivicLens Final Status

Date: 2026-11-05. Repo: https://github.com/insanityatpeak/CivicLens (public). Live: https://civiclens-prns.onrender.com/ (Render free tier).
Stack: FastAPI backend + static single-page frontend; Groq (primary), OpenRouter then Gemini (fallbacks); labeled demonstration fallback.

## Features
**Implemented and verified** (run and seen)
- Three-stage UI (Analyze, Verify, Draft) in headless Chromium at 1280px and 390px: layout, loading, error, empty, no-issue, privacy-warning and Edit/Preview/Copy views were viewed; no console errors, no horizontal overflow.
- Interface controls clicked in a browser: Copy (clipboard contains the user's edits), `.txt` download (UTF-8 BOM, edits kept), `.md` download, Print (print stylesheet hides controls and buttons), English/Hindi switch with the "replace my edits?" confirmation, Hindi download.
- Keyboard-only flow: tab order, a 3px focus ring on every interactive element, Enter and Space activation, flow completed to the Hindi draft.
- Automated accessibility scan (axe-core 4.10) on the draft, error and no-issue views: no violations after fixes (landmark and heading-order findings were fixed).
- Real vision calls through the app: pothole and garbage example photos (Groq, a few seconds); faces flagged on a user photo; a crowded-train photo was classified "Other civic issue" with a privacy note.
- Real English and Hindi drafts through the app and on the live site (Groq); the validator passes them.
- Provider fallback: with Groq forced to fail, OpenRouter answered and the draft passed (single run). Groq 429s during testing also fell through to OpenRouter.
- Validator: injected phone, date, department, unknown source, invented location, unhedged inference, submission claim, inference listed as photo evidence, English words in Hindi text (unit tests, 79 total).
- Friendly provider errors (quota text instead of raw API output) shown in the UI.
- Session analysis cap (tests, with a real-style provider stub).
- Deployed and loaded: https://civiclens-prns.onrender.com/ (garbage example to English draft to Hindi draft, desktop and mobile, no fallback banner).

**Implemented but unverified**
- Camera capture on a real phone; Safari, Firefox and other browsers; any screen reader.
- Hindi interface strings (written by the assistant, no native-speaker review) and Hindi draft quality (readable, judged by the AI assistant only).
- OpenRouter fallback on the live site (verified locally only); OpenRouter first-attempt behaviour (every draft with reasoning off needed the retry; cause not diagnosed because its free daily quota ran out).
- Clarifying question and no-issue decline with a real model (no suitable real photo produced them; verified with the labeled fallback and unit tests).
- Dockerfile and `render.yaml` as a Blueprint (the live service was created by hand following the same commands).
- Print output as a physical page or PDF (print stylesheet checked in emulated print media only).

**Not implemented**
- Real evaluation/metrics (no labeled photo set); face and plate blurring; official reporting-channel links; screenshots in the repo; LICENSE; bring-your-own-key; global rate limiting.

## AI models and keys
- Primary: Groq `qwen/qwen3.8-27b`. Fallback: OpenRouter `nvidia/nemotron-3.5-super-vl:free` (reasoning off). Second fallback: Gemini `gemini-2.5-flash` (wired in; NOT yet run in this configuration, no key set yet). Keys come from environment variables (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`), never committed. Temperature 0.2.
- Free-tier limits observed: Groq 1,000 output and 7,000 input tokens per minute for this model; OpenRouter free models 50 requests per day (1,000 with $10 credit); Gemini free about 20 requests per day (exhausted earlier). Models rotate: two default ids returned 404 and were replaced from live catalogues.

## Files
```
src/civiclens/web/            FastAPI server + static frontend (index.html, app.css, app.js, i18n.js)
src/civiclens/providers/      base, openai_compat (Groq/OpenRouter), chain (fallback), gemini, mock
src/civiclens/                config, schemas, analysis, complaint, safety (validator), i18n, parsing, export, evalmetrics
scripts/                      spike.py, run_pipeline.py
eval/                         run_eval.py, dataset.csv (empty), REPORT.md (no eval run)
tests/                        analysis, safety, complaint, mock/export, eval, providers, web
docs/                         ARCHITECTURE, DECISIONS, UI_DESIGN, PROJECT_STATE, DEPLOY, FINAL_STATUS
data/                         SOURCES.md; samples/pothole.jpg and garbage.jpg (CC0, committed); three user photos stay local
Dockerfile, render.yaml       deployment files
```

## Tests
`79 passed` and ruff clean (2026-11-05). They use scripted, canned or mocked-HTTP providers: they test logic, not model quality. Browser checks were scripted with Playwright (not part of the repo test suite).

## Evaluation
None. `eval/REPORT.md` says so. Real-model checks so far are single runs: Groq English and Hindi drafts on two photos (all validator-pass), OpenRouter Hindi N=8 (all pass after retry, median 7.6 s), no ground-truth labels, same author as the prompts.

## Run locally
`pip install -r requirements.txt`, copy `.env.example` to `.env` and set `GROQ_API_KEY` (and `OPENROUTER_API_KEY`), then `uvicorn civiclens.web.server:app --app-dir src --port 8000`. CLI: `python scripts/run_pipeline.py photo.jpg --lang hi`.

## Deployment
Deployed on Render free tier (instances sleep when idle; shared keys; see limits above). `docs/DEPLOY.md` has steps.

## Known limitations
Vision stage unevaluated; the crowded-train photo was accepted as an "other civic issue" (over-acceptance risk); one observation on a face photo described a person's action although the prompt says not to describe individuals; validator is pattern-based; English and Hindi only; no blurring; provider quotas are the practical ceiling for a public demo; when both providers are throttled users see a "busy" message.

## Remaining user actions
LICENSE; screenshots; confirm rights for the three user-supplied photos before showing them publicly; consider $10 OpenRouter credit or Groq's dev tier before a live demo; native-speaker review of Hindi strings; label a photo set and run `eval/run_eval.py`.
