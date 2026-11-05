# Phase 3 Plan: Product Workflow and UI

## 1. State machine (st.session_state["stage"])
```
upload --Analyze--> analysis --(needs question)--> [answer form] --> context form --Create draft--> draft
   ^                   |  no civic issue: message + "Try another photo"                              |
   +------------------ Start over (clears image + all state) <--------------------------------------+
```
- upload: uploader + preview; errors (wrong type, too big, unreadable, provider down) shown in plain words, uploader stays.
- analysis: plain-words result, privacy warning if faces/plates, evidence ledger. If clarifying question: answer form first (or "use a different photo"). Then context form (location, ongoing, notes, language).
- draft: where-each-statement-comes-from table, editable text, validator warnings, copy + download, neutral "where to send" box.
- Model calls only fire on button clicks and are gated by stage; results live in session_state, so reruns never re-call the model.

## 2. Differentiator in UI
Ledger rows with a tag: green "Seen in photo" / amber "Assumed", plus confidence in words ("fairly sure"). In the draft, a "Where each statement comes from" table links each claim to its ledger entry or "You told us".

## 3. Design direction
Calm, official-but-warm: off-white paper background, deep teal primary, amber reserved for "assumed" and warnings. Type: Inter + Noto Sans Devanagari (Google Fonts) for guaranteed Hindi rendering; 16px base. Spacing scale 4/8/16/24. Cards with 1px border, 10px radius, no gradients or animation. Contrast checked by token choice (teal #0F6B5C on #FAF8F3 about 6:1). Streamlit theme via `.streamlit/config.toml` plus a small CSS block.

## 4. Framework limits
Streamlit styled via config + one CSS string; untrusted model text is HTML-escaped before any `unsafe_allow_html`. No fine pixel control; no frontend-design skill found in this environment, so design is by hand.

## 5. Demo without a key
Real Gemini is unavailable (no key). To let the flow be walked, `MockProvider` now returns *labeled, canned* analysis/complaint JSON for three scenarios (pothole, unclear, no-issue), selectable in the UI. This is NOT AI: a permanent banner says so. Mock only activates via explicit user choice, never silently.

## 6. Trust copy / reporting channel
Disclaimers: AI can be wrong; review before use; draft only, not submitted; photo not stored; privacy notice for faces/plates. "Where to send this": tell user to check their local municipal body's official channel. No portals, numbers or names (none verified).

## Tasks
P0 flow, ledger, clarify, context, EN/HI, edit/copy/download, start over, error handling, rerun gating, labeled mock. P1 theme, how-it-works expander, responsive CSS. Sample-image buttons: NOT possible (no licensed images yet).

## Verification
Streamlit AppTest for flow logic (headless), pytest for export/mock. Visual look: UNVERIFIED unless a browser is used; user to eyeball localhost.
