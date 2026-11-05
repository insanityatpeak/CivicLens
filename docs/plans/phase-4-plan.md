# Phase 4 Plan: Evaluation and Hardening

## State of the world
No GEMINI_API_KEY, no images in data/samples. So: **no real model metrics can be produced this phase.** Build the harness so it runs the moment images + key exist; test the harness itself with the labeled demonstration fallback and mark every such number "HARNESS TEST ONLY, not model performance".

## 1. Metrics (what, how, automated or manual)
| Metric | How | Auto/Manual |
|---|---|---|
| Classification accuracy | counts + per-class + confusion matrix over `split=test` rows | Auto |
| Correct decline/ask | no_civic_issue rows declined; unclear rows got a question or `unclear`; forced-label rate | Auto |
| Field completeness | description, requested_action, >=1 claim present, per language | Auto |
| Unsupported-claim rate | validator issues per draft + first-pass pass rate; manual spot-check sheet for misses | Auto + Manual (pending) |
| Latency | mean, median, p95 over N runs; provider/model recorded | Auto |
| EN/HI quality | 1-5 rubric (fluency, faithfulness, register, actionability) via generated `rating_sheet.csv` | Manual, PENDING (rater: user) |
Failures per image are counted, not hidden.

## 2. Dataset
`eval/dataset.csv` (path, true_label, source, license, split). Header only until the user supplies images. Target: >=6 per class, 3 classes minimum to start (pothole, garbage, no issue) + ambiguous; split dev/test, prompts may only be tuned on dev. Collection checklist in eval/REPORT.md. No fabricated rows.

## 3. Fairness
Only `split=test` is scored by default; run records split. One targeted fix allowed, then rerun on test and report before/after (P1; not possible yet).

## 4. Threats to validity (stated in report)
Tiny N, single labeler, web images easier than phone photos, model version drift, prompt-tuning bias, temperature fixed at 0.2 (not fully deterministic).

## Tasks
P0 `src/civiclens/evalmetrics.py` (pure functions), `eval/run_eval.py`, `eval/REPORT.md`, tests, hardening (ruff, secret scan, fresh-venv install + pytest, dependency check, code review). P1 targeted fix: BLOCKED.
