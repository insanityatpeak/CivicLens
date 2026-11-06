# Phase 2 Plan: AI Core Engine

Inputs: provider abstraction (Phase 1). No API key in env, so real-model behaviour stays UNVERIFIED; pipeline logic is tested with a scripted fake provider.

## Decisions
1. **Pipeline: two stages** (image -> `ImageAnalysis`; analysis + user facts -> `ComplaintDraft`). Alternative: single multimodal call (fewer calls, but seeing and writing mix, so grounding cannot be checked). Chosen two-stage: the writer never sees pixels, only ledger entries, so every claim can be checked against ids.
2. **Taxonomy (closed):** pothole_road_damage, garbage_overflow, stagnant_water, damaged_infrastructure, streetlight_concern, other_civic_issue, no_civic_issue, unclear. `other_civic_issue` = real issue outside the list (still drafts). `unclear` = cannot tell, triggers a question.
3. **Observed vs inferred:** each observation has id (o1..), text, type, confidence (low/medium/high). Observed = visible in pixels. Inferred = anything about cause, function, severity, danger, duration.
4. **Uncertainty policy (enforced in code, after parsing):**
   - `is_civic_issue=false` -> category forced to `no_civic_issue`, no question, no complaint.
   - category `unclear` or `category_confidence=low` -> a clarifying question is required (model's, else a generic default). Complaint generation waits for the answer.
   - otherwise classify. Questions are short and layperson-answerable (prompt rule).
5. **Grounding:** model returns `claim_sources` (statement -> `o<N>` or `user:<field>`). Code validator checks sources exist, inferred claims are hedged, forbidden patterns, no invented location. On failure: regenerate once with the violation list; if still failing, return the draft with warnings (never hidden).
6. **Language:** generate directly in target language (EN/HI), ids stay ASCII. Direct vs translate comparison needs a real model: NOT VERIFIED, revisit when a key exists. Code checks Devanagari ratio for Hindi.
7. **Failure modes:** malformed JSON (one retry), provider error/refusal/empty, oversize (>10 MB), non-image or corrupt file, unsupported format. All raise typed `AnalysisError`/`ComplaintError` with plain messages. Timeouts/rate limits arrive as `ProviderError`.
8. **Privacy (P1):** `privacy_flags` (faces, license_plates) reported by the model; UI warns. Images are re-encoded to JPEG, which drops EXIF/GPS. Auto-blurring: NOT built (no light, reliable option); documented as future work.

## Tasks
- P0 schemas.py, i18n.py, parsing.py, analysis.py, complaint.py, safety.py
- P0 unit tests with a scripted fake provider (pipeline logic, not model quality)
- P0 scripts/run_pipeline.py (real provider integration)
- P1 privacy flags path

## Risks
- Prompts are untested against a real model. Output quality UNVERIFIED.
- Validator heuristics (regex) are best effort, not proof of faithfulness.

## Acceptance
Integration runs per sample image cannot happen (no key, no images): state this plainly.
