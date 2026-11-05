# CivicLens Decisions (Phase 1)

> Historical record of Phase 1 (2026-11-05). The Streamlit stack chosen here was later replaced by FastAPI plus a static frontend, and Gemini by Groq with OpenRouter as fallback: see `docs/UI_DESIGN.md` and `docs/PROJECT_STATE.md`.

Note: the user opted out of discovery questions, so these are the assistant's defaults, not user-agreed choices. Override any of them.

## A. Concept critique
- Weakness of today's process: citizens must pick the right department, category and wording, usually in English, and complaints lack actionable detail (location, ongoing or not).
- Who benefits most: non-English speakers, elderly users, people unsure which body handles what.
- Versus "photo to a general chatbot": CivicLens separates observed from assumed, asks instead of guessing, validates the draft against its evidence, and never invents location, dates or authorities.
- Ambiguous photo: ask one short clarifying question. No civic issue: say so, do not force a category. Faces or plates: show a privacy warning (blurring is future work unless clean).

## B. Three interpretations
| | 1. Evidence-grounded complaint writer | 2. Conversational multilingual grievance assistant | 3. Complaint-quality coach |
|---|---|---|---|
| Originality | High (evidence ledger) | Medium (common chatbot form) | Medium |
| Social impact | High | High | Medium |
| AI depth | Vision + grounded generation + validator | Dialogue + vision | Scoring + rewriting |
| Build effort | Medium | High | Medium |
| Demo strength | High (visible ledger) | Medium | Medium |
| Technical risk | Medium | High | Low |

## C. Chosen: 1, with the evidence ledger as differentiator
Every complaint statement maps to an observation (seen in photo) or a user-supplied fact. Unsupported content is flagged or omitted. Chosen because it is the most checkable, demoable and honest. Elements of 2 (one clarifying question) are kept.

## D. MVP
- Journey: upload photo, analysis, optional clarifying question, optional context (location, ongoing, notes), pick EN/HI, editable draft, copy/download.
- Essential AI: structured image analysis (observed vs inferred, confidence), grounded EN/HI complaint generation, rule-based validator.
- Not built: submission to any government system, accounts, storage of uploads, auto-blurring (future), languages beyond EN/HI (P2), custom model training.

## E. Stack
| Option | Setup | Reliability | Cost | Deploy | Demo | Hindi |
|---|---|---|---|---|---|---|
| Streamlit + multimodal API (chosen) | Fast | Good | Free tier | Easy (Community Cloud) | Good | Good |
| Gradio + multimodal API | Fast | Good | Free tier | Easy (HF Spaces) | Good | Good |
| Streamlit + local models | Slow | Weak on laptop | Free | Hard | Medium | Weak |
| Python backend + light frontend | Slow | Good | Free tier | Medium | Best, most effort | Good |

- Primary provider: Google Gemini (free-tier key, strong multimodal and Hindi). Model name set by `GEMINI_MODEL` env var; default `gemini-2.5-flash` is UNVERIFIED until a key is available.
- Fallback: `MockProvider`, canned text, always labeled as a demonstration fallback.
- `ModelProvider` interface in `src/civiclens/providers/base.py` keeps app logic provider-independent.

## Environment findings (names only, no values)
Python 3.12.10, git 2.52. No GEMINI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY or OPENAI_API_KEY set.
