"""Tests of the eval harness itself. Uses the demonstration fallback on generated images:
these check harness mechanics only and say NOTHING about model performance."""
import csv
import importlib.util
import json
from pathlib import Path

from conftest import jpeg_bytes

from civiclens import evalmetrics as em
from civiclens.providers.mock import MockProvider

_spec = importlib.util.spec_from_file_location("run_eval", Path(__file__).resolve().parents[1] / "eval" / "run_eval.py")
run_eval = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_eval)


def test_percentile_and_latency_stats():
    assert em.percentile([1, 2, 3, 4, 5], 50) == 3
    assert em.percentile([], 95) is None
    s = em.latency_stats([1.0, 2.0, 3.0])
    assert s["n"] == 3 and s["median"] == 2.0 and s["mean"] == 2.0
    assert em.latency_stats([])["n"] == 0


def test_classification_counts_failures_as_wrong():
    rows = [{"true": "a", "pred": "a"}, {"true": "a", "pred": "b"}, {"true": "b", "pred": None}]
    c = em.classification(rows)
    assert c["correct"] == 1 and c["total"] == 3
    assert c["confusion"]["b"] == {"FAILED": 1}
    assert c["per_class"]["a"] == {"correct": 1, "total": 2}


def test_decline_or_ask_metrics():
    rows = [
        {"true": "no_civic_issue", "pred": "no_civic_issue"},
        {"true": "no_civic_issue", "pred": "pothole_road_damage"},
        {"true": "unclear", "pred": "pothole_road_damage", "asked": True},
        {"true": "unclear", "pred": "pothole_road_damage", "asked": False},
    ]
    d = em.decline_or_ask(rows)
    assert (d["no_issue_declined"], d["ambiguous_asked"], d["forced_label"]) == (1, 1, 2)


def _dataset(tmp_path, labels):
    rows = []
    for i, lab in enumerate(labels):
        p = tmp_path / f"img{i}.jpg"
        p.write_bytes(jpeg_bytes())
        rows.append({"path": str(p), "true_label": lab, "source": "generated", "license": "n/a", "split": "test"})
    f = tmp_path / "dataset.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "true_label", "source", "license", "split"])
        w.writeheader()
        w.writerows(rows)
    return f


def test_run_over_images_isolates_failures_and_summarizes(tmp_path):
    ds = _dataset(tmp_path, ["pothole_road_damage", "no_civic_issue"])
    rows = run_eval.read_dataset(ds, "test")
    rows.append({"path": str(tmp_path / "missing.jpg"), "true_label": "pothole_road_damage", "split": "test"})
    recs = [run_eval.evaluate_row(MockProvider("pothole"), r, ["en", "hi"]) for r in rows]
    assert recs[2]["error"]  # missing file counted, run not aborted
    m = run_eval.summarize(recs, ["en", "hi"])
    assert m["n_images"] == 3 and m["n_failed_analysis"] == 1
    assert m["classification"]["total"] == 3
    assert m["complaints"]["en"]["n"] >= 1


def test_empty_dataset_reports_and_evaluates_nothing(tmp_path, capsys, monkeypatch):
    f = tmp_path / "d.csv"
    f.write_text("path,true_label,source,license,split\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["run_eval", "--dataset", str(f), "--out", str(tmp_path / "out")])
    assert run_eval.main() == 3
    assert "nothing was evaluated" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_fallback_runs_are_stamped_harness_only(tmp_path, monkeypatch):
    ds = _dataset(tmp_path, ["pothole_road_damage"])
    monkeypatch.setenv("CIVICLENS_PROVIDER", "mock")
    monkeypatch.setattr("sys.argv", ["run_eval", "--dataset", str(ds), "--out", str(tmp_path / "out")])
    assert run_eval.main() == 0
    run_dir = next((tmp_path / "out").iterdir())
    assert "HARNESS TEST ONLY" in (run_dir / "REPORT.md").read_text(encoding="utf-8")
    meta = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))["meta"]
    assert meta["harness_test_only"] is True
    assert (run_dir / "rating_sheet.csv").exists() and (run_dir / "summary.csv").exists()
