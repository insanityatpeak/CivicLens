# Architecture

CivicLens turns a photo of a civic problem into an editable complaint draft in which every statement is traceable to its source.

## Flow
1. **Validate** (`web/server.py`, `analysis.py`): size and type check, resize, re-encode with Pillow (drops EXIF/GPS). Photos are not stored.
2. **Stage 1, vision** (`analysis.py`): a vision model returns *observations*, each marked `observed` or `inferred` with a confidence, plus category and privacy flags (faces, number plates).
3. **Uncertainty policy** (`analysis.py`, plain code, not the model): no civic issue -> stop with "nothing to report"; unsure -> ask one clarifying question; otherwise continue.
4. **User details**: location, whether it is ongoing, free-text notes, output language (EN/HI).
5. **Stage 2, writing** (`complaint.py`): a text model sees only the ledger entries and the user's facts, never the pixels, and produces a draft plus a claim table that cites ledger ids.
6. **Grounding validator** (`safety.py`, rule-based): flags invented phone numbers, dates, departments, links and locations, claims of submission, inferences stated as fact, unknown source ids, and English text in Hindi drafts. On failure the draft is regenerated once; remaining warnings are shown.
7. **Output**: editable draft with a "where each statement comes from" table; copy or download as `.txt` / `.md`.

## Modules
| Path | Role |
|---|---|
| `src/civiclens/web/` | FastAPI server and static single-page frontend (`index.html`, `app.css`, `app.js`, `i18n.js`); no build step |
| `src/civiclens/providers/` | `ModelProvider` interface; `openai_compat` (Groq, OpenRouter), `gemini`, `chain` (fallback), `mock` |
| `src/civiclens/` | `config`, `schemas` (Pydantic), `analysis`, `complaint`, `safety`, `i18n`, `parsing`, `export`, `evalmetrics` |
| `eval/` | Evaluation harness and report template (no labeled dataset yet) |
| `tests/` | Logic and HTTP-level tests using scripted or canned providers |

## Providers
Groq is primary, then OpenRouter, then Gemini. `FallbackChain` moves to the next provider only when a call fails (quota, network, refusal). App logic never depends on a specific model; ids are set in `.env`. A labeled, canned **demonstration fallback** (not AI, ignores the photo) exists for walking the flow without a key and activates only when chosen.

## Design decisions
See [DECISIONS.md](DECISIONS.md) (historical rationale), [UI_DESIGN.md](UI_DESIGN.md) and [DEPLOY.md](DEPLOY.md).
