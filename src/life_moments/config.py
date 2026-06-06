"""Central configuration: enums, thresholds, model names, and runtime settings.

These mirror the classification schema and operating parameters described in the
capstone report (Sections VII, IX and Appendices B, G, M).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class RecoverabilityClass(str, Enum):
    """Top-level recoverability label produced by the classifier (Appendix B)."""

    HIGH_POTENTIAL = "High-Potential"
    LOW_POTENTIAL = "Low-Potential"
    RELEASE = "Release"


class LifeContext(str, Enum):
    """Life-context categories (Section VII.3 / Appendix B). NONE == no signal."""

    BUDGET_PRESSURE = "Budget Pressure"
    SCHEDULE_CHANGE = "Schedule Change"
    HEALTH_EVENT = "Health Event"
    WORK_TRAVEL = "Work Travel"
    NEW_ARRIVAL = "New Arrival"
    RELOCATION = "Relocation"
    OTHER = "Other"
    NONE = "None"


class Sentiment(str, Enum):
    """Brand-sentiment orientation of the comment (Appendix D)."""

    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class PriorityBand(str, Enum):
    """Priority-score bands that drive the urgency triage in Section VII.2."""

    URGENT = "Urgent"        # 75-100  -> outreach within 24h, CRM-flagged
    HIGH = "High"            # 50-74   -> automated outreach within 48-72h
    MODERATE = "Moderate"    # 25-49   -> scheduled re-engagement sequence
    LOW = "Low"              # 0-24    -> scheduled re-engagement sequence


# --- Operating thresholds (Section IX.3 pre-launch validation checks) ----------

# Outputs below this confidence are routed to human review rather than acted upon.
CONFIDENCE_THRESHOLD = 0.6

# Comments shorter than this (after stripping) are treated as un-classifiable.
MIN_COMMENT_CHARS = 12

# Phase-1 silent-validation exit gate (Section IX.2): AI/human agreement target.
PHASE1_AGREEMENT_GATE = 0.75


def priority_band(score: int) -> PriorityBand:
    """Map a 0-100 priority score onto a triage band."""
    if score >= 75:
        return PriorityBand.URGENT
    if score >= 50:
        return PriorityBand.HIGH
    if score >= 25:
        return PriorityBand.MODERATE
    return PriorityBand.LOW


# --- Model selection (Section IX.3) --------------------------------------------
# The report recommends Claude Sonnet 4.6 (Batch API) for routine classification
# and reserves Claude Opus 4.6 for cases escalated to human review.
DEFAULT_CLASSIFIER_MODEL = "claude-sonnet-4-6"
ESCALATION_MODEL = "claude-opus-4-6"


# --- Pre-screen vocabulary (Section IX.1 "filter before classifying") ----------
# Comments containing none of this vocabulary and tagged as product/quality
# complaints can skip the LLM call entirely (~74% cost reduction in the report).
LIFE_CONTEXT_VOCAB: dict[LifeContext, tuple[str, ...]] = {
    LifeContext.BUDGET_PRESSURE: (
        "afford", "budget", "money", "tight", "expensive cost", "cash",
        "save money", "cutting back", "between jobs", "lost my job", "laid off",
        "pricey right now", "financ", "broke",
    ),
    LifeContext.SCHEDULE_CHANGE: (
        "schedule", "busy", "no time", "too hectic", "new job", "new shift",
        "hours changed", "overwhelmed", "back to school", "semester",
    ),
    LifeContext.HEALTH_EVENT: (
        "surgery", "recovery", "recovering", "diagnos", "doctor", "medical",
        "illness", "hospital", "injury", "treatment", "health issue",
    ),
    LifeContext.WORK_TRAVEL: (
        "travel", "traveling", "travelling", "on the road", "out of town",
        "business trip", "deployment", "away for work", "relocating temporarily",
    ),
    LifeContext.NEW_ARRIVAL: (
        "baby", "newborn", "pregnan", "expecting", "maternity", "new arrival",
        "having a kid", "just had a",
    ),
    LifeContext.RELOCATION: (
        "moving", "move", "relocat", "new city", "new apartment", "new house",
        "changing address",
    ),
    LifeContext.OTHER: (
        "personal", "family emergency", "life got", "going through",
        "circumstances", "for now", "temporar",
    ),
}

# Positive / negative sentiment cues used by the offline heuristic classifier.
POSITIVE_CUES = (
    "love", "loved", "great", "delicious", "amazing", "best", "favorite",
    "favourite", "miss", "will be back", "be back", "come back", "return",
    "wonderful", "fantastic", "enjoyed", "highly recommend", "wish i could",
    "hope to", "temporarily", "for now",
)
NEGATIVE_CUES = (
    "disappointed", "terrible", "awful", "hate", "worst", "bland", "tasteless",
    "overpriced", "rip off", "ripoff", "not worth", "repetitive", "boring",
    "poor quality", "bad", "never again", "cancel for good", "done with",
    "waste",
)
# Comment language signalling explicit intent to return.
RETURN_INTENT_CUES = (
    "be back", "come back", "return", "resubscribe", "rejoin", "once things",
    "when i can", "in a few", "hope to", "will sign up again", "see you",
)
# Product-retention anchors (Section V.5) that strengthen an offer.
RETENTION_ANCHORS = (
    "taste", "flavor", "flavour", "variety", "quality", "organic", "recipes",
    "ingredients", "portion", "seasoning",
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings, populated from environment variables."""

    anthropic_api_key: str | None = None
    classifier_model: str = DEFAULT_CLASSIFIER_MODEL
    escalation_model: str = ESCALATION_MODEL
    use_batch_api: bool = True
    backend: str = "auto"  # "auto" | "anthropic" | "heuristic"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
            classifier_model=os.getenv("LIFE_MOMENTS_MODEL", DEFAULT_CLASSIFIER_MODEL),
            escalation_model=os.getenv("LIFE_MOMENTS_ESCALATION_MODEL", ESCALATION_MODEL),
            use_batch_api=os.getenv("LIFE_MOMENTS_USE_BATCH", "1") not in ("0", "false", "False"),
            backend=os.getenv("LIFE_MOMENTS_BACKEND", "auto"),
        )
