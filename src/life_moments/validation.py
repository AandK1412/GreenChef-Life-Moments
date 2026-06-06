"""Output validation (Section IX.3 / Appendix M).

Four code-level checks run on every classifier output before it is acted upon.
Per the report's principle "enforce safety rules in code", correctness is never
trusted to the prompt alone:

1. Format check         - output parsed into the typed schema.
2. Classification check - enum values are valid; score in range.
3. Confidence check     - outputs below 0.6 are routed to human review.
4. Evidence grounding   - the cited evidence span must actually appear in the
                          comment (catches hallucinated justifications).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import CONFIDENCE_THRESHOLD, LifeContext, RecoverabilityClass
from .schemas import Classification


@dataclass
class ValidationResult:
    ok: bool
    needs_human_review: bool
    reasons: list[str] = field(default_factory=list)

    @property
    def reason(self) -> str | None:
        return "; ".join(self.reasons) if self.reasons else None


def validate(classification: Classification, comment: str) -> ValidationResult:
    """Run the four checks. Returns a `ValidationResult`.

    A failure does not raise — it flags the record for human review so the
    cancellation always completes normally (Risk register, Appendix M.2).
    """
    reasons: list[str] = []
    needs_review = False

    # 1 & 2. Format + classification validity. By construction a `Classification`
    # instance already passed pydantic validation, but we re-assert invariants
    # that the schema cannot express on its own.
    if not (0 <= classification.priority_score <= 100):
        reasons.append("priority_score out of range")
    if not (0.0 <= classification.confidence <= 1.0):
        reasons.append("confidence out of range")
    # A High-Potential label with no life context is internally inconsistent.
    if (
        classification.recoverability is RecoverabilityClass.HIGH_POTENTIAL
        and classification.life_context is LifeContext.NONE
    ):
        reasons.append("High-Potential without a life-context category")
        needs_review = True

    # 3. Confidence check.
    if classification.confidence < CONFIDENCE_THRESHOLD:
        reasons.append(f"confidence {classification.confidence:.2f} < {CONFIDENCE_THRESHOLD}")
        needs_review = True

    # 4. Evidence grounding (hallucination detection). If an evidence span was
    # supplied it must be a literal substring of the comment.
    evidence = (classification.evidence or "").strip()
    if evidence and evidence.lower() not in (comment or "").lower():
        reasons.append("evidence span not found in comment (possible hallucination)")
        needs_review = True

    ok = not needs_review
    return ValidationResult(ok=ok, needs_human_review=needs_review, reasons=reasons)
