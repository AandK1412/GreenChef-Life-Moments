"""Pre-screen filter (Section IX.1 "filter before classifying").

Before any LLM call, a cheap word-matching pass decides whether a comment is
worth sending to the model. Comments with no life-context vocabulary that read
as pure product/quality complaints, or comments that are too short to classify,
are short-circuited here. The report attributes ~74% of the AI-cost reduction to
this step.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import (
    LIFE_CONTEXT_VOCAB,
    MIN_COMMENT_CHARS,
    NEGATIVE_CUES,
    LifeContext,
    RecoverabilityClass,
    Sentiment,
)
from .schemas import Classification


@dataclass
class PreScreenResult:
    """Outcome of the pre-screen pass for one comment."""

    send_to_llm: bool
    # If send_to_llm is False, a short-circuit classification is supplied.
    shortcut: Classification | None = None
    matched_contexts: tuple[LifeContext, ...] = ()


def _matched_contexts(text: str) -> tuple[LifeContext, ...]:
    low = text.lower()
    hits = []
    for ctx, vocab in LIFE_CONTEXT_VOCAB.items():
        if any(token in low for token in vocab):
            hits.append(ctx)
    return tuple(hits)


def pre_screen(comment: str) -> PreScreenResult:
    """Decide whether `comment` should be sent to the LLM classifier.

    Returns a `PreScreenResult`. When `send_to_llm` is False a deterministic
    short-circuit `Classification` is attached so the record is still labelled.
    """
    text = (comment or "").strip()

    # Too short / empty -> Release without an AI call.
    if len(text) < MIN_COMMENT_CHARS:
        return PreScreenResult(
            send_to_llm=False,
            shortcut=Classification(
                recoverability=RecoverabilityClass.RELEASE,
                life_context=LifeContext.NONE,
                sentiment=Sentiment.NEUTRAL,
                priority_score=0,
                confidence=0.9,
                evidence=text,
                rationale="Comment too short to classify; pre-screen short-circuit.",
            ),
        )

    contexts = _matched_contexts(text)
    low = text.lower()
    has_negative = any(cue in low for cue in NEGATIVE_CUES)

    # No life-context vocabulary at all: pure product/quality complaint.
    # Classify as Low-Potential without an AI call.
    if not contexts:
        return PreScreenResult(
            send_to_llm=False,
            shortcut=Classification(
                recoverability=RecoverabilityClass.LOW_POTENTIAL,
                life_context=LifeContext.NONE,
                sentiment=Sentiment.NEGATIVE if has_negative else Sentiment.NEUTRAL,
                priority_score=10 if has_negative else 20,
                confidence=0.7,
                evidence="",
                rationale="No life-context signal detected; pre-screen short-circuit.",
            ),
            matched_contexts=contexts,
        )

    # Life-context vocabulary present -> worth a full classification.
    return PreScreenResult(send_to_llm=True, matched_contexts=contexts)
