"""Stage 1: image -> structured ImageAnalysis."""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps
from pydantic import ValidationError

from .parsing import extract_json
from .providers.base import ModelProvider, ProviderError
from .schemas import ImageAnalysis

MAX_BYTES = 10 * 1024 * 1024
MAX_SIDE = 1568
MAX_PIXELS = 40_000_000  # decompression-bomb guard: refuse to decode anything larger
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

DEFAULT_QUESTION = "Could you tell us what problem you want to report in this photo, and where it is?"

ANALYSIS_PROMPT = """You are analysing a photo a citizen took to report a civic issue.
Reply with ONE JSON object only, no other text, with exactly these keys:
{
  "category": one of "pothole_road_damage","garbage_overflow","stagnant_water","damaged_infrastructure","streetlight_concern","other_civic_issue","no_civic_issue","unclear",
  "category_confidence": "low"|"medium"|"high",
  "observations": [{"id":"o1","text":"short description","type":"observed"|"inferred","confidence":"low"|"medium"|"high"}],
  "risks_visible": [short strings, only risks you can actually see],
  "missing_info": [short strings, details needed to act on this that the photo cannot show],
  "clarifying_question": null, or ONE short question a layperson can answer,
  "privacy_flags": subset of ["faces","license_plates"] that are visible,
  "is_civic_issue": true|false
}
Rules:
- "observed" means directly visible in the pixels. Anything about cause, whether something works, severity, danger or duration is "inferred".
- Number observation ids o1, o2, ... in order.
- If you cannot tell what the issue is, use category "unclear" and ask a clarifying_question. Do not guess.
- If the photo shows no civic problem, set is_civic_issue false and category "no_civic_issue".
- Never identify or describe individual people. Only flag that faces or license plates are visible.
- Do not invent locations, dates, or authorities."""


class AnalysisError(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


@dataclass
class AnalysisResult:
    analysis: ImageAnalysis
    model: str
    latency_s: float
    is_fallback: bool


def prepare_image(data: bytes) -> bytes:
    """Validate, orient, downsize and re-encode as JPEG (drops EXIF incl. GPS)."""
    if not data:
        raise AnalysisError("invalid_image", "The file is empty.")
    if len(data) > MAX_BYTES:
        raise AnalysisError("too_large", f"The image is larger than {MAX_BYTES // (1024 * 1024)} MB. Please use a smaller photo.")
    try:
        opened = Image.open(io.BytesIO(data))
        fmt = opened.format
        if fmt not in ALLOWED_FORMATS:
            raise AnalysisError("unsupported_type", "Please upload a JPEG, PNG or WEBP photo.")
        if opened.width * opened.height > MAX_PIXELS:
            raise AnalysisError("too_large", "That photo has too many pixels. Please use a smaller photo.")
        img = ImageOps.exif_transpose(opened)
        img = img.convert("RGB")
    except AnalysisError:
        raise
    except Image.DecompressionBombError as exc:
        raise AnalysisError("too_large", "That photo has too many pixels. Please use a smaller photo.") from exc
    except Exception as exc:
        raise AnalysisError("invalid_image", "That file could not be read as an image.") from exc
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


def apply_uncertainty_policy(a: ImageAnalysis) -> ImageAnalysis:
    """Enforce, in code, when to stop, ask, or classify."""
    if not a.is_civic_issue or a.category == "no_civic_issue":
        return a.model_copy(update={"category": "no_civic_issue", "is_civic_issue": False, "clarifying_question": None})
    if a.category == "unclear" or a.category_confidence == "low":
        q = (a.clarifying_question or "").strip() or DEFAULT_QUESTION
        return a.model_copy(update={"clarifying_question": q})
    return a


def analyze_image(provider: ModelProvider, image_bytes: bytes, mime_type: str = "image/jpeg") -> AnalysisResult:
    prepared = prepare_image(image_bytes)
    prompt = ANALYSIS_PROMPT
    last_error = ""
    total_latency = 0.0
    for attempt in range(2):
        try:
            res = provider.generate(prompt, prepared, "image/jpeg")
        except ProviderError as exc:
            raise AnalysisError("provider", f"The AI service could not be reached or declined the request: {exc}") from exc
        total_latency += res.latency_s
        try:
            analysis = ImageAnalysis.model_validate(extract_json(res.text))
            return AnalysisResult(apply_uncertainty_policy(analysis), res.model, total_latency, res.is_fallback)
        except (ValueError, ValidationError) as exc:
            last_error = str(exc)
            prompt = ANALYSIS_PROMPT + f"\n\nYour previous reply was invalid ({last_error[:300]}). Reply with valid JSON only."
    raise AnalysisError("malformed_output", "The AI returned an answer we could not read. Please try again.")
