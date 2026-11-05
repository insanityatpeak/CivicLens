"""Stage 2: ImageAnalysis + UserContext + language -> grounded ComplaintDraft."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from .i18n import language_name_for_prompt, validate_language
from .parsing import extract_json
from .providers.base import ModelProvider, ProviderError
from .safety import ValidationReport, validate_draft
from .schemas import ComplaintDraft, ImageAnalysis, UserContext

COMPLAINT_PROMPT = """You write a citizen's complaint DRAFT about a civic issue. You cannot see the photo; you only have the evidence ledger below.
Write all text in {language}. Keep observation ids (o1, o2...) and "user:<field>" source tags in ASCII.
Reply with ONE JSON object only with keys:
{{"description": str, "location": str or null, "observed_evidence": [str], "public_impact": str, "requested_action": str,
  "claim_sources": [{{"statement": str, "source": "o<N>" or "user:<field>"}}], "missing_info": [str]}}
Rules:
- State only what is in observations of type "observed" or in the user facts. Inferred observations may appear only in hedged wording ("may", "could pose a risk").
- Every entry in observed_evidence must also appear, word for word, as a "statement" in claim_sources with its source.
- location: use the user's location_text exactly; if none was given set null and add "location" to missing_info.
- NEVER invent a location, date, injury, severity, department, authority, phone number, email or link.
- When writing Hindi, translate every word, including technical terms. Do not leave English words or parenthesised English in the text; the only exception is text copied from the user facts.
- Do not say the complaint was submitted or registered. It is a draft for the user to review.
- Be polite, short and specific. requested_action should ask for inspection and repair/cleanup without naming an authority.

Issue category: {category}
Evidence ledger (JSON): {ledger}
User facts (JSON): {user}
"""


class ComplaintError(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


@dataclass
class ComplaintResult:
    draft: ComplaintDraft
    report: ValidationReport
    warnings: list[str] = field(default_factory=list)
    latency_s: float = 0.0
    regenerated: bool = False
    is_fallback: bool = False


def _build_prompt(analysis: ImageAnalysis, ctx: UserContext, language: str, violations: list[str] | None) -> str:
    ledger = [o.model_dump() for o in analysis.observations]
    prompt = COMPLAINT_PROMPT.format(
        language=language_name_for_prompt(language),
        category=analysis.category,
        ledger=json.dumps(ledger, ensure_ascii=False),
        user=json.dumps(ctx.provided_fields(), ensure_ascii=False),
    )
    if violations:
        prompt += "\nYour previous draft broke these rules; fix them:\n- " + "\n- ".join(violations)
    return prompt


def _generate_once(provider: ModelProvider, prompt: str, analysis: ImageAnalysis, language: str):
    try:
        res = provider.generate(prompt)
    except ProviderError as exc:
        raise ComplaintError("provider", f"The AI service could not be reached or declined the request: {exc}") from exc
    try:
        data = extract_json(res.text)
        data.update(issue_category=analysis.category, language=language, is_draft=True)
        return ComplaintDraft.model_validate(data), res
    except (ValueError, ValidationError):
        return None, res


def generate_complaint(provider: ModelProvider, analysis: ImageAnalysis, ctx: UserContext, language: str = "en") -> ComplaintResult:
    validate_language(language)
    if not analysis.is_civic_issue or analysis.category == "no_civic_issue":
        raise ComplaintError("no_issue", "No civic issue was detected, so there is nothing to draft.")
    if analysis.category == "unclear" and not ctx.clarification_answer:
        raise ComplaintError("needs_clarification", analysis.clarifying_question or "More information is needed.")

    violations: list[str] | None = None
    latency = 0.0
    draft = report = None
    fallback = False
    for attempt in range(2):
        draft, res = _generate_once(provider, _build_prompt(analysis, ctx, language, violations), analysis, language)
        latency += res.latency_s
        fallback = res.is_fallback
        if draft is None:
            violations = ["Reply was not valid JSON matching the required keys."]
            continue
        report = validate_draft(draft, analysis, ctx, language)
        if report.passed:
            return ComplaintResult(draft, report, [], latency, attempt == 1, fallback)
        violations = report.messages()
    if draft is None or report is None:
        raise ComplaintError("malformed_output", "The AI returned a draft we could not read. Please try again.")
    return ComplaintResult(draft, report, report.messages(), latency, True, fallback)
