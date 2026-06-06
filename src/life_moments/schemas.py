"""Typed schemas for classifier I/O.

`Classification` is the structured object every backend (LLM or heuristic) must
return. `RoutedRecord` is the fully enriched record emitted by the pipeline.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .config import (
    LifeContext,
    PriorityBand,
    RecoverabilityClass,
    Sentiment,
    priority_band,
)


class Classification(BaseModel):
    """The structured result for a single cancellation comment.

    This is the JSON contract the LLM is prompted to return (Appendix G/M) and
    the object the offline heuristic backend produces as well.
    """

    recoverability: RecoverabilityClass
    life_context: LifeContext = LifeContext.NONE
    sentiment: Sentiment = Sentiment.NEUTRAL
    priority_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    return_intent: bool = False
    # A short verbatim span from the comment that justifies the label. Used by
    # the evidence-grounding check to catch hallucinated classifications.
    evidence: str = ""
    rationale: str = ""

    @field_validator("evidence", "rationale", mode="before")
    @classmethod
    def _none_to_empty(cls, v: object) -> object:
        return "" if v is None else v

    @property
    def band(self) -> PriorityBand:
        return priority_band(self.priority_score)


class RoutedRecord(BaseModel):
    """A classified comment plus its routing decision and review flag."""

    order_id: str
    week: int
    comment: str
    classification: Classification
    track_name: str
    primary_offer: str
    secondary_action: str
    outreach_sla: str
    channel: str
    needs_human_review: bool = False
    review_reason: str | None = None
    sent_to_classifier: bool = False  # passed the pre-screen (cost-bearing path)
    used_llm: bool = False             # an actual LLM API call was made

    def flat(self) -> dict:
        """Flatten to a single-level dict suitable for a CSV/DataFrame row."""
        c = self.classification
        return {
            "order_id": self.order_id,
            "week": self.week,
            "comment": self.comment,
            "recoverability": c.recoverability.value,
            "life_context": c.life_context.value,
            "sentiment": c.sentiment.value,
            "priority_score": c.priority_score,
            "priority_band": c.band.value,
            "return_intent": c.return_intent,
            "confidence": round(c.confidence, 3),
            "evidence": c.evidence,
            "track_name": self.track_name,
            "primary_offer": self.primary_offer,
            "secondary_action": self.secondary_action,
            "outreach_sla": self.outreach_sla,
            "channel": self.channel,
            "needs_human_review": self.needs_human_review,
            "review_reason": self.review_reason or "",
            "sent_to_classifier": self.sent_to_classifier,
            "used_llm": self.used_llm,
        }
