"""Extract a JSON object from model text."""
from __future__ import annotations

import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> dict:
    """Parse the first JSON object in `text` (handles code fences and surrounding prose)."""
    m = _FENCE.search(text)
    candidate = m.group(1) if m else text
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    obj = json.loads(candidate[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("Model output JSON is not an object.")  # noqa: TRY004  (callers catch ValueError)
    return obj
