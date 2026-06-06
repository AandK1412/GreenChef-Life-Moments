"""Prompt specification for the LLM classification layer (Appendix G / M).

The instruction template is cacheable (Section IX.1 "cache the instruction
template") — it is constant across calls so it can be sent once with prompt
caching enabled and reused, cutting the cost of the repeated instruction
portion by up to ~90%.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are the classification layer of the Green Chef "Life Moments" subscriber
retention system. You read a single subscriber cancellation comment and decide
how recoverable that subscriber is, why they are leaving, and how urgently the
retention team should respond.

You must reason about FOUR rubric dimensions (Appendix G.1):
1. Temporariness  - is the departure reason likely to resolve within ~12 weeks?
2. Externality    - is the cause a life circumstance rather than dissatisfaction
                    with the product itself?
3. Emotional tone - does the comment express positive/neutral or negative
                    sentiment toward Green Chef?
4. Relationship   - does the comment suggest the subscriber valued the product
                    before leaving?

RECOVERABILITY CLASSES:
- High-Potential : temporary, externally-driven exit with neutral/positive
                   sentiment. Recoverable with a calibrated offer.
- Low-Potential  : exit driven mainly by product dissatisfaction (price, taste,
                   fundamental misalignment). Standard win-back unlikely to work.
- Release        : insufficient signal to classify reliably.

LIFE-CONTEXT CATEGORIES (choose at most one, or "None"):
Budget Pressure, Schedule Change, Health Event, Work Travel, New Arrival,
Relocation, Other.

PRIORITY INTERVENTION SCORE (0-100): higher reflects a stronger combination of
positive brand sentiment, an explicit life-context signal, and expressed intent
to return.

EVIDENCE RULE: the "evidence" field MUST be a short span copied VERBATIM from the
comment. Never invent or paraphrase evidence. If no span supports the label,
return an empty string and lower your confidence.

Respond with ONLY a JSON object, no preamble and no markdown fences:
{
  "recoverability": "High-Potential" | "Low-Potential" | "Release",
  "life_context":  "Budget Pressure" | "Schedule Change" | "Health Event" |
                   "Work Travel" | "New Arrival" | "Relocation" | "Other" | "None",
  "sentiment":     "Positive" | "Neutral" | "Negative",
  "priority_score": <integer 0-100>,
  "return_intent":  true | false,
  "confidence":     <float 0.0-1.0>,
  "evidence":       "<verbatim span from the comment, or empty string>",
  "rationale":      "<one short sentence>"
}
"""

# A handful of few-shot anchors keep the model calibrated on the sentiment-
# divergence diagnostic (Section V.4): same exit reason, opposite recoverability.
FEW_SHOT_EXAMPLES = [
    (
        "I absolutely love these meals but money is really tight this month and "
        "I just can't justify it right now. Hope to be back soon!",
        {
            "recoverability": "High-Potential",
            "life_context": "Budget Pressure",
            "sentiment": "Positive",
            "priority_score": 88,
            "return_intent": True,
            "confidence": 0.93,
            "evidence": "money is really tight this month",
            "rationale": "Temporary cash-flow constraint with strong positive sentiment and explicit return intent.",
        },
    ),
    (
        "Way too expensive for what you get and the recipes got repetitive. "
        "Not worth it.",
        {
            "recoverability": "Low-Potential",
            "life_context": "None",
            "sentiment": "Negative",
            "priority_score": 8,
            "return_intent": False,
            "confidence": 0.9,
            "evidence": "Not worth it",
            "rationale": "Permanent value objection and product dissatisfaction, negative sentiment.",
        },
    ),
    (
        "Traveling for work for the next two months, will resubscribe when I'm back.",
        {
            "recoverability": "High-Potential",
            "life_context": "Work Travel",
            "sentiment": "Neutral",
            "priority_score": 72,
            "return_intent": True,
            "confidence": 0.88,
            "evidence": "Traveling for work for the next two months",
            "rationale": "Time-bounded external circumstance with explicit return intent.",
        },
    ),
]


def build_user_message(comment: str) -> str:
    return f"Classify this subscriber cancellation comment:\n\n{comment.strip()}"
