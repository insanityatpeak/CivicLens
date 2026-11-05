# Phase 1 Plan

Decisions and rationale: see `docs/DECISIONS.md`.

## Tasks
- P0: scaffold, .gitignore, .env.example, requirements, config.py
- P0: provider interface, Gemini provider, mock fallback
- P0: scripts/spike.py, run it and record the truth
- P0: data/SOURCES.md and sourcing checklist (no invented images)
- P1: Streamlit skeleton

## Risks
- No API key in this environment: real spike cannot run until user adds GEMINI_API_KEY.
- Model name default unverified.
- Sample images must be sourced by the user (no network image licensing check done here).

## Acceptance
