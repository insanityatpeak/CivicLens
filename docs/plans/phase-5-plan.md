# Phase 5 Plan: README, Repo, Deployment

## 1. README strategy
Above the fold (top ~20 lines): title + tagline, one-paragraph problem, one-paragraph solution, the differentiator in one sentence (evidence ledger: every claim tagged "Seen in photo" / "Assumed" / "You told us"), honest status line (prototype; no real-model evaluation yet), run command. No screenshot yet (none captured): a "Screenshots pending" note, not a fake image.

## 2. Evidence inventory (claim -> support)
| Claim | Support |
|---|---|
| Two-stage pipeline, closed taxonomy, uncertainty policy | src/civiclens/analysis.py, complaint.py; tests/test_analysis.py |
| Validator catches invented phone/date/department/location, unknown sources, unhedged inference, submission claims | src/civiclens/safety.py; tests/test_safety.py |
| EN/HI draft flow works end to end | tests/test_app_flow.py (labeled fallback only) |
| 50 tests pass, lint clean, fresh-venv install works | PROJECT_STATE.md verification log |
| Gemini integration | code written; NOT VERIFIED (no key) |
| Hindi quality, accuracy, latency | NONE: stated as not evaluated |
| Deployed | No: NOT DEPLOYED |

## 3. Deployment options
| | Streamlit Community Cloud | Hugging Face Spaces |
|---|---|---|
| Free tier | yes | yes |
| Secrets | app secrets (exposed as env vars) | Space secrets (env vars) |
| Build | reads requirements.txt | needs README header / Dockerfile or Streamlit SDK |
| Cold start | sleeps when idle | sleeps when idle |
Choose **Streamlit Community Cloud**: no extra files, matches the framework. Needs the user's GitHub + Streamlit account; I prepare `docs/DEPLOY.md` with exact steps. Status: NOT DEPLOYED.

## 4. Public-demo risk mitigations
Implemented: 10 MB upload cap (existing), soft per-session cap of 10 real-model analyses (app.py), explicit labeled fallback banner. Documented, not built: bring-your-own-key field, global rate limiting, spending cap on the key (user should set a quota in Google AI Studio).

## 5. Screenshots plan
No browser capture was done. Expected filenames: 01-upload, 02-evidence-ledger, 03-clarifying-question, 04-draft-en, 05-draft-hi, 06-no-issue. README shows none until they exist.

## Open items needing the user
