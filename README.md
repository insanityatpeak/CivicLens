# CivicLens

*See a Problem. Report a Solution.*


**Code:** https://github.com/insanityatpeak/CivicLens · **Live demo:** not deployed yet


> **Status: working prototype.** The full flow runs and is tested (52 passing tests). It has **not** yet been evaluated against a real model or a labeled photo set, and it is **not deployed**. See [Evaluation](#evaluation-results) and [Limitations](#limitations).

## The problem
Reporting a pothole, a garbage pile or stagnant water is a hassle: you must pick the right category, find the right department, write a convincing complaint, often in a language that is not your own, and include details (where? how long?) that you may not think about. So most issues go unreported.

## The solution
A citizen uploads a photo. CivicLens lists what the AI can **see** and what it only **assumes**, asks one short question if it is unsure, then writes an editable complaint **draft** in English or Hindi. Nothing is submitted anywhere; the user reviews, edits and sends it themselves.

## What makes it different: the evidence ledger
- **Every claim is traceable.** Each statement in the draft is tagged *Seen in photo*, *Assumed* or *You told us*.
- **It asks instead of guessing.** An unclear photo triggers a clarifying question; a photo with no civic issue gets a plain "nothing to report", not a forced label.
- **Code checks the AI.** A rule-based validator flags invented phone numbers, dates, departments, links and locations, claims that the complaint was "submitted", and inferences stated as fact. On failure the draft is regenerated once; remaining warnings are shown to the user.
- **Privacy-aware.** Photos are re-encoded (dropping EXIF/GPS), not stored by the app, and a warning appears if faces or number plates are reported.


## AI/ML architecture
```mermaid
flowchart LR
  P[Photo] --> V[Validate, resize,<br/>strip EXIF]
  V --> S1[Stage 1: vision model<br/>-> observations<br/>observed / inferred + confidence]
  S1 --> U{Uncertainty policy<br/>in code}
  U -- no civic issue --> N[Stop: nothing to report]
  U -- unsure --> Q[Ask 1 clarifying question]
  Q --> C
  U -- clear --> C[User details<br/>location, ongoing, notes]
  C --> S2[Stage 2: text model<br/>ledger + user facts -> draft<br/>EN / HI]
  S2 --> G[Grounding validator<br/>rule-based]
  G -- fail --> R[Regenerate once] --> G
  G --> D[Editable draft + source table<br/>+ warnings]
```
- **Two stages** separate *seeing* from *writing*: the writer never sees pixels, only ledger entries, so claims can be checked against ids.
- **Provider abstraction** (`ModelProvider`): Gemini is the primary provider; swapping models does not touch app logic.
- **Demonstration fallback:** a clearly labeled, canned offline mode so the flow can be walked without a key. It is **not AI**, never looks at the photo, and only activates when you choose it.

## Technology stack
Python 3.12 · FastAPI + Uvicorn (backend) · vanilla HTML/CSS/JS single-page frontend (no build step) · Google Gemini via `google-genai` (primary provider, default model `gemini-2.5-flash`, configurable) · Pydantic · Pillow · pytest · ruff.

## Installation and setup
```
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
# edit .env and set GEMINI_API_KEY (free key: https://aistudio.google.com/apikey)
```
Never commit `.env`. For development tools: `pip install -r requirements-dev.txt`.

## Run locally
```
uvicorn civiclens.web.server:app --app-dir src --port 8000
# then open http://localhost:8000
```
No key yet? Click **Use demonstration fallback** in the app (it appears when no key is set), or set `CIVICLENS_PROVIDER=mock`. Other commands:
```
python scripts/spike.py [image]                     # one real model call + Hindi check
python scripts/run_pipeline.py photo.jpg --lang hi  # full pipeline in the terminal
pytest                                              # 58 tests (logic, not model quality)
```

## How to use
1. Upload a photo of the problem and click **Analyze photo**.
2. Read the **evidence ledger**. Answer the question if one is asked.
3. Add where it is, whether it is ongoing, and any notes; pick English or Hindi.
4. Review and edit the draft, check *where each statement comes from*, then copy or download it (`.txt` / `.md`).
5. Find your local municipal body's official channel to send it. CivicLens does not know or verify contact details.

## Evaluation results
**No real evaluation has been run.** There is no labeled photo set yet, so there are no accuracy, latency or Hindi-quality numbers to report. A small smoke test (not an evaluation) did run the real Gemini model on the complaint-writing stage using a hand-written pothole ledger: 3 drafts (English with location, Hindi with location, English without location) all passed the validator on the first try and invented nothing. The photo-reading (vision) stage has not been run against a real model. The harness exists and is tested: `python eval/run_eval.py --split test` (see [`eval/REPORT.md`](eval/REPORT.md) for the dataset checklist, method and threats to validity). Runs on the demonstration fallback are stamped *harness test only*.

What *is* verified (see `docs/PROJECT_STATE.md` for exact commands and outputs): 52 unit and UI-flow tests pass, including injected fabrications being caught by the validator; lint is clean; install works in a fresh virtual environment; a scan found no secrets in the tree or git history. These tests use a scripted or canned provider, so they say nothing about model quality.

## Limitations
- Real-model behavior is barely measured: category accuracy from real photos, the vision prompt, Hindi quality beyond 3 smoke-test drafts, and whether generating Hindi directly beats translating are all **unmeasured**.
- The validator is pattern-based. It catches the listed fabrication types but cannot prove a draft is faithful.
- Only English and Hindi. Only still photos. No location from the photo (EXIF is stripped on purpose).
- Face and number-plate **blurring is not implemented**; the app only warns.
- The per-session usage cap is soft, not a global rate limit. A shared API key on a public deployment can still be exhausted.
- UI visuals and mobile layout have not been checked in a real browser.
- The Gemini free tier allowed about 20 requests per day for this model when tested (quota ran out during testing), and one analysis plus one draft uses 2 requests. A shared public demo would exhaust it quickly.
- Not deployed.

## Responsible AI and privacy
- Output is a **prediction and a draft**, never a confirmed finding or an official submission. No government system is contacted.
- The model is told not to identify people or invent locations, dates, injuries, severity, departments or contact details; code enforces this.
- Photos are processed in the session and not stored by CivicLens. Note that the model provider receives the image to analyze it, and photos may contain faces or number plates.
- Secrets live in environment variables only.

## Future enhancements
Verified links to official reporting channels; more Indian languages; face and plate blurring; optional geotagging from EXIF with explicit consent; bring-your-own-key and server-side rate limiting; a citizen-to-authority feedback loop.

## AI-assisted development disclosure

## License
[License: to be chosen by the team. MIT is a common default.]

## Acknowledgments
Sample image sources and licenses: see `data/SOURCES.md` (no images added yet).
