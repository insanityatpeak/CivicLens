"""Run the pipeline over eval/dataset.csv and write real, traceable results.

Usage: python eval/run_eval.py [--split test] [--langs en,hi] [--dataset eval/dataset.csv]
Outputs: eval/results/<timestamp>/{<n>.json, summary.csv, metrics.json, REPORT.md, rating_sheet.csv}
If the provider is the demonstration fallback, everything is stamped HARNESS TEST ONLY.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8", errors="replace")  # Hindi output on Windows consoles

sys.path.insert(0, str(ROOT / "src"))

from civiclens import evalmetrics as em
from civiclens.analysis import AnalysisError, analyze_image
from civiclens.complaint import ComplaintError, generate_complaint
from civiclens.config import ConfigError, load_settings
from civiclens.providers import get_provider
from civiclens.schemas import UserContext

TEMPERATURE = 0.2  # fixed in providers/gemini.py; recorded here for the report


def read_dataset(path: Path, split: str) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("split") == split]


def evaluate_row(provider, row: dict, langs: list[str]) -> dict:
    rec: dict = {"path": row["path"], "true": row["true_label"], "pred": None, "asked": False, "error": None,
                 "analysis_latency_s": None, "complaints": {}}
    try:
        data = (ROOT / row["path"]).read_bytes()
        ar = analyze_image(provider, data)
    except (AnalysisError, OSError) as exc:
        rec["error"] = getattr(exc, "message", str(exc))
        return rec
    a = ar.analysis
    rec.update(pred=a.category, asked=bool(a.clarifying_question), analysis_latency_s=ar.latency_s,
               confidence=a.category_confidence, analysis=a.model_dump())
    if not a.is_civic_issue or a.clarifying_question:
        return rec  # nothing to draft: declined or waiting for an answer
    for lang in langs:
        try:
            cr = generate_complaint(provider, a, UserContext(), lang)
            d = cr.draft
            rec["complaints"][lang] = {
                "passed": cr.report.passed, "n_issues": len(cr.report.issues), "regenerated": cr.regenerated,
                "complete": bool(d.description.strip() and d.requested_action.strip() and d.claim_sources),
                "latency_s": cr.latency_s, "warnings": cr.warnings, "draft": d.model_dump(),
            }
        except ComplaintError as exc:
            rec["complaints"][lang] = {"error": exc.message}
    return rec


def summarize(records: list[dict], langs: list[str]) -> dict:
    cls_rows = [{"true": r["true"], "pred": r["pred"], "asked": r["asked"]} for r in records]
    lat = [r["analysis_latency_s"] for r in records if r["analysis_latency_s"] is not None]
    per_lang = {}
    for lang in langs:
        cs = [c for r in records if (c := r["complaints"].get(lang)) and "error" not in c]
        lat += [c["latency_s"] for c in cs]
        per_lang[lang] = em.complaint_stats(cs)
        per_lang[lang]["errors"] = sum(1 for r in records if "error" in r["complaints"].get(lang, {}))
    return {
        "n_images": len(records),
        "n_failed_analysis": sum(1 for r in records if r["error"]),
        "classification": em.classification(cls_rows),
        "decline_or_ask": em.decline_or_ask(cls_rows),
        "complaints": per_lang,
        "latency_s": em.latency_stats(lat),
    }


def render_report(meta: dict, m: dict) -> str:
    stamp = "> **HARNESS TEST ONLY: demonstration fallback was used. These numbers are NOT model performance.**\n\n" if meta["is_fallback"] else ""
    c = m["classification"]
    acc = f"{c['correct']}/{c['total']}" + (f" = {c['accuracy']:.0%}" if c["accuracy"] is not None else "")
    d = m["decline_or_ask"]
    lat = m["latency_s"]
    lines = [
        "# Evaluation Report (generated)", "", stamp,
        f"- Date (UTC): {meta['date']}\n- Provider/model: {meta['provider']} / {meta['model']}\n- Temperature: {meta['temperature']}",
        f"- Split: {meta['split']}; images: {m['n_images']}; failed analyses: {m['n_failed_analysis']}",
        "- Labeling: single labeler (dataset author). Automated metrics only; manual ratings pending (see rating_sheet.csv).", "",
        f"## Classification\nAccuracy: **{acc}** (counts, small N; see metrics.json for per-class and confusion).", "",
        f"## Decline / ask\n- Non-civic declined: {d['no_issue_declined']}/{d['no_issue_total']}\n- Ambiguous asked a question: {d['ambiguous_asked']}/{d['ambiguous_total']}\n- Forced a label on non-civic/ambiguous: {d['forced_label']}/{d['forced_label_denominator']}", "",
        "## Complaints (automated)",
    ]
    for lang, s in m["complaints"].items():
        if s.get("n"):
            lines.append(f"- {lang}: n={s['n']}, complete={s['complete']}, validator pass (final)={s['validator_passed_final']}, first try={s['passed_first_try']}, issues flagged={s['total_issues_flagged']}, errors={s['errors']}")
        else:
            lines.append(f"- {lang}: no drafts generated (errors={s['errors']})")
    f = lambda v: "n/a" if v is None else f"{v:.2f}s"
    lines += ["", f"## Latency (N={lat['n']} calls)\nmean {f(lat['mean'])}, median {f(lat['median'])}, p95 {f(lat['p95'])}", "",
              "## Limitations\nTiny N; single labeler; web images easier than phone photos; model version drift; validator is heuristic and can miss fabrications (spot-check pending); prompts must only be tuned on dev split."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(ROOT / "eval" / "dataset.csv"))
    ap.add_argument("--split", default="test")
    ap.add_argument("--langs", default="en,hi")
    ap.add_argument("--out", default=str(ROOT / "eval" / "results"))
    a = ap.parse_args()
    langs = [x for x in a.langs.split(",") if x]
    rows = read_dataset(Path(a.dataset), a.split)
    if not rows:
        print(f"No rows with split={a.split!r} in {a.dataset}. Add labeled images (see eval/REPORT.md checklist); nothing was evaluated.")
        return 3
    try:
        provider = get_provider()
        settings = load_settings()
    except (ConfigError, ValueError) as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = Path(a.out) / ts
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for i, row in enumerate(rows):
        rec = evaluate_row(provider, row, langs)
        records.append(rec)
        (out / f"{i:03d}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{i + 1}/{len(rows)}] {row['path']}: true={rec['true']} pred={rec['pred']} err={rec['error']}")
    models = {"groq": settings.groq_model, "openrouter": settings.openrouter_model, "gemini": settings.gemini_model}
    # A fallback chain may answer from any of its providers; the configured order is recorded instead of guessing.
    model = ", ".join(f"{n}={models.get(n, n)}" for n in settings.providers)
    meta = {"date": ts, "provider": provider.name, "model": model, "temperature": TEMPERATURE,
            "split": a.split, "is_fallback": provider.is_fallback, "harness_test_only": provider.is_fallback}
    metrics = summarize(records, langs)
    (out / "metrics.json").write_text(json.dumps({"meta": meta, "metrics": metrics}, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "true", "pred", "asked", "error", "analysis_latency_s", *[f"{l}_validator_passed" for l in langs]])
        for r in records:
            w.writerow([r["path"], r["true"], r["pred"], r["asked"], r["error"], r["analysis_latency_s"],
                        *[r["complaints"].get(l, {}).get("passed", "") for l in langs]])
    with (out / "rating_sheet.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "lang", "fluency_1to5", "faithfulness_1to5", "register_1to5", "actionability_1to5", "missed_fabrication_yes_no", "rater"])
        for r in records:
            for lang in r["complaints"]:
                w.writerow([r["path"], lang, "", "", "", "", "", ""])
    (out / "REPORT.md").write_text(render_report(meta, metrics), encoding="utf-8")
    print(f"\nResults written to {out}")
    print(render_report(meta, metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
