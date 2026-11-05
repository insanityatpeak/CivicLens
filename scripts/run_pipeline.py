"""Full pipeline with the configured (real) provider. Usage: python scripts/run_pipeline.py image.jpg --lang hi [--location "..."] [--answer "..."]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civiclens.analysis import AnalysisError, analyze_image
from civiclens.complaint import ComplaintError, generate_complaint
from civiclens.config import ConfigError
from civiclens.providers import get_provider
from civiclens.schemas import UserContext


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--lang", default="en", choices=["en", "hi"])
    ap.add_argument("--location")
    ap.add_argument("--ongoing", action="store_true")
    ap.add_argument("--notes")
    ap.add_argument("--answer", help="answer to a clarifying question")
    a = ap.parse_args()
    try:
        provider = get_provider()
    except (ConfigError, ValueError) as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    if provider.is_fallback:
        print("*** DEMONSTRATION FALLBACK: not real AI; pipeline will likely fail to parse canned text. ***")
    try:
        ar = analyze_image(provider, Path(a.image).read_bytes())
    except AnalysisError as exc:
        print(f"ANALYSIS ERROR [{exc.kind}]: {exc.message}")
        return 1
    print(f"== ANALYSIS (model={ar.model}, {ar.latency_s:.2f}s) ==")
    print(ar.analysis.model_dump_json(indent=2))
    if ar.analysis.privacy_flags:
        print(f"PRIVACY WARNING: {ar.analysis.privacy_flags} visible in photo.")
    if not ar.analysis.is_civic_issue:
        print("Result: no civic issue detected.")
        return 0
    ctx = UserContext(location_text=a.location, ongoing=True if a.ongoing else None, notes=a.notes, clarification_answer=a.answer)
    if ar.analysis.clarifying_question and not a.answer:
        print(f"CLARIFYING QUESTION: {ar.analysis.clarifying_question}\n(re-run with --answer to continue)")
        return 0
    try:
        cr = generate_complaint(provider, ar.analysis, ctx, a.lang)
    except ComplaintError as exc:
        print(f"COMPLAINT ERROR [{exc.kind}]: {exc.message}")
        return 1
    print(f"== COMPLAINT DRAFT ({a.lang}, {cr.latency_s:.2f}s, regenerated={cr.regenerated}) ==")
    print(cr.draft.model_dump_json(indent=2))
    print(f"== VALIDATOR: {'PASS' if cr.report.passed else 'FAIL'} ==")
    for m in cr.warnings:
        print(" -", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
