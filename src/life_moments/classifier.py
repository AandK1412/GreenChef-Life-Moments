"""The classification layer (Capability 1, Section VII.2).

Two interchangeable backends implement the same `Classifier` protocol:

* `AnthropicClassifier` - calls Claude (Sonnet 4.6 by default) with the
  Appendix-M prompt, with prompt caching and optional Batch API usage. Requires
  the `anthropic` package and an API key.
* `HeuristicClassifier` - a deterministic, dependency-free rule engine that
  reproduces the same schema offline. It lets the whole pipeline, the tests, and
  CI run with no API key, and serves as a transparent baseline.

`get_classifier()` picks a backend based on settings/availability.
"""

from __future__ import annotations

import json
import re
from typing import Protocol

from .config import (
    NEGATIVE_CUES,
    POSITIVE_CUES,
    RETENTION_ANCHORS,
    RETURN_INTENT_CUES,
    LifeContext,
    RecoverabilityClass,
    Sentiment,
    Settings,
)
from .prescreen import _matched_contexts
from .prompts import FEW_SHOT_EXAMPLES, SYSTEM_PROMPT, build_user_message
from .schemas import Classification


class Classifier(Protocol):
    name: str

    def classify(self, comment: str) -> Classification: ...


# --- Offline heuristic backend -------------------------------------------------

# When several life-context cues match, prefer the more specific circumstance.
_CONTEXT_PRIORITY = (
    LifeContext.HEALTH_EVENT,
    LifeContext.NEW_ARRIVAL,
    LifeContext.RELOCATION,
    LifeContext.WORK_TRAVEL,
    LifeContext.SCHEDULE_CHANGE,
    LifeContext.BUDGET_PRESSURE,
    LifeContext.OTHER,
)


def _count_hits(text: str, cues: tuple[str, ...]) -> int:
    return sum(1 for c in cues if c in text)


def _pick_context(contexts: tuple[LifeContext, ...]) -> LifeContext:
    for ctx in _CONTEXT_PRIORITY:
        if ctx in contexts:
            return ctx
    return LifeContext.NONE


def _first_evidence(text: str, cues: tuple[str, ...]) -> str:
    low = text.lower()
    for c in cues:
        idx = low.find(c)
        if idx >= 0:
            # Return the original-cased slice around the matched cue.
            return text[idx: idx + len(c)]
    return ""


class HeuristicClassifier:
    """Deterministic rule-based classifier (no network, no dependencies)."""

    name = "heuristic"

    def classify(self, comment: str) -> Classification:
        text = (comment or "").strip()
        low = text.lower()

        contexts = _matched_contexts(text)
        context = _pick_context(contexts)

        pos = _count_hits(low, POSITIVE_CUES)
        neg = _count_hits(low, NEGATIVE_CUES)
        if pos > neg:
            sentiment = Sentiment.POSITIVE
        elif neg > pos:
            sentiment = Sentiment.NEGATIVE
        else:
            sentiment = Sentiment.NEUTRAL

        return_intent = any(c in low for c in RETURN_INTENT_CUES)
        anchor = any(a in low for a in RETENTION_ANCHORS)

        # Recoverability from the four-dimensional rubric.
        if context is LifeContext.NONE:
            recoverability = RecoverabilityClass.LOW_POTENTIAL
        elif sentiment is Sentiment.NEGATIVE:
            # Cites a reason but is angry at the product -> not recoverable.
            recoverability = RecoverabilityClass.LOW_POTENTIAL
        else:
            recoverability = RecoverabilityClass.HIGH_POTENTIAL

        # Priority intervention score (0-100).
        score = 0
        score += {Sentiment.POSITIVE: 35, Sentiment.NEUTRAL: 20, Sentiment.NEGATIVE: 5}[sentiment]
        score += 25 if context is not LifeContext.NONE else 0
        score += 25 if return_intent else 0
        score += 10 if anchor else 0
        score = max(0, min(100, score))
        if recoverability is RecoverabilityClass.LOW_POTENTIAL:
            score = min(score, 30)

        # Confidence grows with the number of corroborating cues.
        cue_strength = (pos + neg) + (1 if context is not LifeContext.NONE else 0) + (1 if return_intent else 0)
        confidence = min(0.95, 0.6 + 0.08 * cue_strength)

        evidence = (
            _first_evidence(text, FromContextCues.get(context, ()))
            or _first_evidence(text, POSITIVE_CUES if sentiment is Sentiment.POSITIVE else NEGATIVE_CUES)
        )

        return Classification(
            recoverability=recoverability,
            life_context=context,
            sentiment=sentiment,
            priority_score=score,
            return_intent=return_intent,
            confidence=round(confidence, 3),
            evidence=evidence,
            rationale=f"Heuristic rubric: context={context.value}, sentiment={sentiment.value}.",
        )


# Map each life context to the vocabulary used to surface evidence spans.
from .config import LIFE_CONTEXT_VOCAB as _VOCAB  # noqa: E402

FromContextCues = {ctx: vocab for ctx, vocab in _VOCAB.items()}


# --- Anthropic backend ---------------------------------------------------------


class AnthropicClassifier:
    """Calls Claude with the Appendix-M prompt and parses the JSON result."""

    name = "anthropic"

    def __init__(self, settings: Settings):
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:  # pragma: no cover - exercised only with the dep
            raise RuntimeError(
                "The 'anthropic' package is required for the LLM backend. "
                "Install it with `pip install anthropic`, or use the heuristic "
                "backend (set LIFE_MOMENTS_BACKEND=heuristic)."
            ) from exc
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")

        self._anthropic = __import__("anthropic")
        self._client = self._anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.classifier_model

    def _messages(self, comment: str) -> list[dict]:
        msgs: list[dict] = []
        for example_comment, example_json in FEW_SHOT_EXAMPLES:
            msgs.append({"role": "user", "content": build_user_message(example_comment)})
            msgs.append({"role": "assistant", "content": json.dumps(example_json)})
        msgs.append({"role": "user", "content": build_user_message(comment)})
        return msgs

    def classify(self, comment: str) -> Classification:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=400,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                # Cache the constant instruction template (Section IX.1).
                "cache_control": {"type": "ephemeral"},
            }],
            messages=self._messages(comment),
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
        return parse_classification(text)


def parse_classification(raw: str) -> Classification:
    """Parse a (possibly fenced) JSON classification string into the schema."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {raw!r}")
    data = json.loads(match.group(0))
    return Classification(**data)


def get_classifier(settings: Settings | None = None) -> Classifier:
    """Return the configured backend, falling back to the heuristic one."""
    settings = settings or Settings.from_env()
    if settings.backend == "heuristic":
        return HeuristicClassifier()
    if settings.backend == "anthropic":
        return AnthropicClassifier(settings)
    # auto: use Anthropic if a key is present and the package is importable.
    if settings.anthropic_api_key:
        try:
            return AnthropicClassifier(settings)
        except RuntimeError:
            pass
    return HeuristicClassifier()
