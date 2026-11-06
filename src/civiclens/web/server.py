"""FastAPI backend + static single-page frontend.

The server is stateless apart from a per-session analysis counter (soft quota guard). The AI pipeline
(analysis -> uncertainty policy -> grounded complaint -> rule-based validator) is imported unchanged.
"""
from __future__ import annotations

import logging
import secrets
import threading
from collections import Counter
from pathlib import Path
from typing import Annotated, get_args

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..analysis import MAX_BYTES, AnalysisError, analyze_image
from ..complaint import ComplaintError, generate_complaint
from ..config import ConfigError
from ..export import draft_to_text
from ..i18n import CATEGORY_LABELS, SUPPORTED
from ..providers import get_provider
from ..providers.base import ModelProvider
from ..providers.mock import SCENARIOS, MockProvider
from ..schemas import Category, ImageAnalysis, Language, UserContext

ROOT = Path(__file__).resolve().parents[3]
STATIC = Path(__file__).parent / "static"
SAMPLES_DIR = ROOT / "data" / "samples"
MAX_RUNS_PER_SESSION = 10  # soft cap on real-model analyses per browser session (not a global rate limit)

# Example photos offered on the empty state. Only files that exist and have a recorded license are listed.
SAMPLES: dict[str, dict[str, str | None]] = {
    "pothole": {"file": "pothole.jpg", "demo_scenario": "pothole"},
    "garbage": {"file": "garbage.jpg", "demo_scenario": None},
}

log = logging.getLogger("civiclens")
app = FastAPI(title="CivicLens", docs_url=None, redoc_url=None)

_runs: Counter[str] = Counter()
_runs_lock = threading.Lock()


# ---------- helpers ----------
def _provider(demo: str | None) -> ModelProvider:
    if demo:
        if demo not in SCENARIOS:
            raise HTTPException(400, "Unknown demonstration scenario.")
        return MockProvider(demo)
    try:
        return get_provider()
    except (ConfigError, ValueError) as exc:
        raise HTTPException(503, detail={"kind": "config", "message": str(exc)}) from exc


def _sid(request: Request) -> str:
    return request.cookies.get("cl_sid") or ""


def friendly(kind: str, message: str) -> tuple[str, str]:
    """Map pipeline errors to citizen-readable text. Raw provider detail goes to the server log only."""
    if kind == "provider":
        log.warning("provider error: %s", message)
        low = message.lower()
        if "429" in low or "resource_exhausted" in low or "quota" in low:
            return "quota", "The AI service is busy or has reached its usage limit. Please wait a few minutes and try again."
        return "provider", "The AI service could not be reached right now. Please check your connection and try again in a moment."
    return kind, message


def _err(status: int, kind: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"kind": kind, "message": message}}, status_code=status)


@app.exception_handler(HTTPException)
async def _http_exc(_: Request, exc: HTTPException) -> JSONResponse:
    d = exc.detail
    if isinstance(d, dict) and "kind" in d:
        return _err(exc.status_code, d["kind"], d["message"])
    return _err(exc.status_code, "request", str(d))


# ---------- API ----------
@app.get("/api/status")
def status(request: Request, response: Response) -> dict:
    if not request.cookies.get("cl_sid"):
        response.set_cookie("cl_sid", secrets.token_urlsafe(16), httponly=True, samesite="lax")
    configured, message = True, None
    try:
        get_provider()
    except (ConfigError, ValueError) as exc:
        configured, message = False, str(exc)
    sid = _sid(request)
    return {
        "configured": configured,
        "config_message": message,
        "max_runs": MAX_RUNS_PER_SESSION,
        "runs_used": _runs.get(sid, 0) if sid else 0,
        "demo_scenarios": list(SCENARIOS),
        "languages": SUPPORTED,
        "category_labels": CATEGORY_LABELS,
        "categories": list(get_args(Category)),
        "samples": [
            {"id": k, "url": f"/samples/{v['file']}", "demo_scenario": v["demo_scenario"]}
            for k, v in SAMPLES.items() if (SAMPLES_DIR / str(v["file"])).is_file()
        ],
    }


@app.post("/api/analyze")
def analyze(request: Request, file: Annotated[UploadFile | None, File()] = None,
            sample: Annotated[str | None, Form()] = None, demo: Annotated[str | None, Form()] = None) -> dict:
    provider = _provider(demo or None)
    if sample:
        meta = SAMPLES.get(sample)
        path = SAMPLES_DIR / str(meta["file"]) if meta else None
        if not path or not path.is_file():
            raise HTTPException(404, "Unknown example photo.")
        data = path.read_bytes()
    elif file is not None:
        data = file.file.read(MAX_BYTES + 1)
    else:
        raise HTTPException(400, "No photo was provided.")

    sid = _sid(request) or "anon"
    if not provider.is_fallback:
        with _runs_lock:
            if _runs[sid] >= MAX_RUNS_PER_SESSION:
                raise HTTPException(429, detail={
                    "kind": "limit",
                    "message": f"This session has used its {MAX_RUNS_PER_SESSION} photo analyses. Please try again later."})
            _runs[sid] += 1
    try:
        res = analyze_image(provider, data)
    except AnalysisError as exc:
        status_code = 502 if exc.kind in ("provider", "malformed_output") else 422
        k, m = friendly(exc.kind, exc.message)
        raise HTTPException(status_code, detail={"kind": k, "message": m}) from exc
    return {"analysis": res.analysis.model_dump(), "model": res.model, "latency_s": round(res.latency_s, 2),
            "is_fallback": res.is_fallback, "runs_used": _runs.get(sid, 0)}


class ComplaintRequest(BaseModel):
    analysis: ImageAnalysis
    language: Language = "en"
    demo: str | None = None
    location_text: str | None = Field(None, max_length=500)
    ongoing: bool | None = None
    notes: str | None = Field(None, max_length=2000)
    clarification_answer: str | None = Field(None, max_length=500)
    # User corrections to the evidence ledger (only ever remove observations or relabel the category).
    category: Category | None = None
    observation_ids: list[str] | None = None


def apply_corrections(a: ImageAnalysis, category: str | None, keep_ids: list[str] | None) -> ImageAnalysis:
    update: dict = {}
    if keep_ids is not None:
        known = {o.id for o in a.observations}
        keep = [i for i in keep_ids if i in known]
        update["observations"] = [o for o in a.observations if o.id in keep]
    if category and category != a.category:
        update.update(category=category, category_confidence="high", is_civic_issue=category != "no_civic_issue")
    return a.model_copy(update=update) if update else a


@app.post("/api/complaint")
def complaint(req: ComplaintRequest) -> dict:
    provider = _provider(req.demo)
    analysis = apply_corrections(req.analysis, req.category, req.observation_ids)
    if not any(o.type == "observed" for o in analysis.observations):
        raise HTTPException(422, detail={"kind": "no_evidence",
                                         "message": "Keep at least one thing the photo shows, so the complaint has evidence to rest on."})
    ctx = UserContext(
        location_text=(req.location_text or "").strip() or None,
        ongoing=req.ongoing,
        notes=(req.notes or "").strip() or None,
        clarification_answer=(req.clarification_answer or "").strip() or None,
    )
    try:
        cr = generate_complaint(provider, analysis, ctx, req.language)
    except ComplaintError as exc:
        code = 502 if exc.kind in ("provider", "malformed_output") else 422
        k, m = friendly(exc.kind, exc.message)
        raise HTTPException(code, detail={"kind": k, "message": m}) from exc

    obs = {o.id: o for o in analysis.observations}
    sources = []
    for c in cr.draft.claim_sources:
        if c.source.startswith("user:"):
            kind = "user"
        elif c.source in obs and obs[c.source].type == "observed":
            kind = "seen"
        else:
            kind = "assumed"
        sources.append({"statement": c.statement, "kind": kind})
    return {
        "text": draft_to_text(cr.draft),
        "language": req.language,
        "sources": sources,
        "missing_info": cr.draft.missing_info,
        "passed": cr.report.passed,
        "warnings": cr.warnings,
        "regenerated": cr.regenerated,
        "is_fallback": cr.is_fallback,
    }


# ---------- static frontend ----------
@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/samples/{name}", include_in_schema=False)
def sample_file(name: str) -> FileResponse:
    allowed = {v["file"] for v in SAMPLES.values()}
    if name not in allowed or not (SAMPLES_DIR / name).is_file():
        raise HTTPException(404, "Not found")
    return FileResponse(SAMPLES_DIR / name)


app.mount("/static", StaticFiles(directory=STATIC), name="static")
