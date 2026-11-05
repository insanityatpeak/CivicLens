# CivicLens UI design (Phase 7)

## Approaches considered
| | A. Restyle Streamlit | B. FastAPI + static single-page frontend (chosen by the user) |
|---|---|---|
| Fit for the brief | Possible with heavy CSS overrides on Streamlit's DOM; split panels, a document-paper preview, real tabs and focus handling fight the framework | Full control of layout, focus management, ARIA, print CSS, Devanagari fonts |
| Cost | Low; keeps AppTest suite and Streamlit Cloud deploy | Rewrite of the frontend and its tests; new deploy story |
| Risk | Brittle selectors across Streamlit upgrades | More code to own, no component library |

The assistant recommended A for cost; the user chose B. B is the stronger fit for a public-facing product, and it is what was built.
Frontend stack: vanilla JS, no build step (nothing to compile or break at deploy time); Inter + Noto Sans/Serif Devanagari + Source Serif 4 via Google Fonts with system fallbacks (Nirmala UI, Mangal).

## What was kept
`analysis.py`, `complaint.py`, `safety.py`, providers, the uncertainty policy and the rule-based grounding validator are unchanged. The server only adapts them to HTTP.

## Visual system
Navy `#0b2545` (chrome, headings), teal `#0e7c7b` (primary actions, "seen" evidence), off-white `#f6f7f4` page, white surfaces with 1px borders and 14px radii, amber for "assumed", red reserved for the demonstration banner and errors. Complaint preview is a serif "paper" with a DRAFT - NOT SUBMITTED stamp, to read as a document rather than a form.

## Flow
1. **Analyze**: drag-and-drop zone, "Take photo" (mobile camera via `capture`), example photos, three-step explainer. Loading state shows named steps.
2. **Verify**: photo beside findings. Observations split into *What the photo shows* and *Possible concerns* (assumed), each with a checkbox so users can remove wrong items; issue type is correctable; a *Confirmed by you* list fills live; the clarifying question appears only when the model is unsure; details form (location, still there, notes, language).
3. **Draft**: persistent "THIS IS A DRAFT" bar, Preview/Edit/Copy views, EN/हिन्दी switch (regenerates from the same evidence; asks before discarding edits), copy, .txt (UTF-8 BOM for Windows Notepad), .md, print/PDF, source list, validator result, "where to send" note.

## Grounding rules preserved
User corrections can only *remove* observations or *relabel* the category; they never add model-visible claims. At least one observed item must remain. Every draft still passes through `validate_draft`.

## Known limits
- Interface strings are in English and Hindi. The Hindi strings were written by the assistant and **have not been reviewed by a native speaker**. Model-generated observation text is English regardless of UI language (the model analysis prompt is English); only the complaint itself is translated.
- Real-model draft and Hindi translation through this UI were **not** verified: the Gemini free-tier quota ran out mid-session (see verification log).
- No cross-browser testing beyond headless Chromium; no screen-reader testing; automated axe-core scan only.
