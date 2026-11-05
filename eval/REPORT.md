# Evaluation Report

**Status: NO REAL EVALUATION HAS BEEN RUN.** No API key and no labeled images were available. There are no model performance numbers in this repository. Do not quote any.

## How to produce real numbers
1. Add images under `data/samples/` (or `eval/images/`), record each in `data/SOURCES.md` (source + license).
2. Add one row per image to `eval/dataset.csv`: `path,true_label,source,license,split`.
   - `true_label` is one of: pothole_road_damage, garbage_overflow, stagnant_water, damaged_infrastructure, streetlight_concern, other_civic_issue, no_civic_issue, unclear.
   - `split`: `dev` (you may tune prompts on these) or `test` (never tune on these).
   - Suggested minimum: 6 images per class for pothole, garbage, no issue, ambiguous; own phone photos preferred.
3. Put `GEMINI_API_KEY` in `.env`, then run: `python eval/run_eval.py --split test`
4. Results land in `eval/results/<timestamp>/` (per-image JSON, `summary.csv`, `metrics.json`, `REPORT.md`, `rating_sheet.csv`). Copy real numbers here with N and method.
5. Fill `rating_sheet.csv` by hand (1-5: fluency, faithfulness, register, actionability) and note who rated; also mark any fabrication the validator missed.

## What the harness measures
Classification accuracy (counts, per-class, confusion); correct decline of non-civic and question-asking on ambiguous images; draft completeness; validator pass and issue counts; latency mean/median/p95. Failed images are counted, not dropped.

## What is manual / pending
English and Hindi quality ratings and the unsupported-claim spot-check. Pending until a rater fills the sheet.

## Threats to validity (will apply to any future numbers)
Small N; single labeler; web images may be easier than real phone photos; model version drift; prompt-tuning bias (hence the dev/test split); temperature 0.2 is low but not fully deterministic; the validator is heuristic and can miss fabrications.

## Harness self-test
The harness was exercised with the demonstration fallback on generated placeholder images in unit tests only. Those runs say nothing about model quality.
