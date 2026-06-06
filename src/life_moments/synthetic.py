"""Synthetic cancellation-comment generator.

The capstone SOW (Appendix H) states that *structurally representative dummy
datasets* were used for all public-facing materials and code development, with
real client data confined to internal analysis under NDA. This module generates
exactly such a dummy dataset: no real subscriber data is used or reproduced.

The latent class mix is tuned to the report's Q1 2026 headline figures
(Appendix E): ~21.86% High-Potential, ~68.02% Low-Potential, ~10.1% Release,
across 8 weeks, with Budget Pressure as the dominant life-context category.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from .config import LifeContext

# Headline mix from Appendix E.
P_HIGH = 0.2186
P_LOW = 0.6802
P_RELEASE = 1.0 - P_HIGH - P_LOW  # ~0.1012

# Relative weights of life-context categories among High-Potential subscribers,
# proportional to the dominant-category counts in Section V.4.
HIGH_CONTEXT_WEIGHTS: dict[LifeContext, float] = {
    LifeContext.BUDGET_PRESSURE: 2439,
    LifeContext.SCHEDULE_CHANGE: 723,
    LifeContext.OTHER: 543,
    LifeContext.WORK_TRAVEL: 251,
    LifeContext.HEALTH_EVENT: 224,
    LifeContext.RELOCATION: 107,
    LifeContext.NEW_ARRIVAL: 42,
}

# Comment templates per life context. Each is written so the offline heuristic
# classifier recovers the intended label. {ret} optionally appends return intent.
HIGH_TEMPLATES: dict[LifeContext, list[str]] = {
    LifeContext.BUDGET_PRESSURE: [
        "I absolutely love these meals but money is really tight right now and I can't afford it this month.{ret}",
        "The food quality is great, just need to cut back on spending until my finances recover.{ret}",
        "Money's tight after some unexpected bills. The recipes are wonderful though.{ret}",
        "Between jobs at the moment so I have to watch my budget. Loved the organic ingredients.{ret}",
    ],
    LifeContext.SCHEDULE_CHANGE: [
        "Started a new job with crazy hours and I have no time to cook right now. The meals were delicious.{ret}",
        "My schedule got really hectic this semester, just too busy to keep up. Great variety though.{ret}",
        "New shift means I'm never home for dinner. I really enjoyed the recipes.{ret}",
    ],
    LifeContext.HEALTH_EVENT: [
        "Recovering from surgery and my doctor changed my diet for now. The meals were great while they lasted.{ret}",
        "Going through a medical treatment and can't manage cooking at the moment. Loved the quality.{ret}",
        "Health issue means I need a different diet temporarily. Wonderful food otherwise.{ret}",
    ],
    LifeContext.WORK_TRAVEL: [
        "Traveling for work for the next two months so I have to pause. The meals were fantastic.{ret}",
        "On the road for a long business trip, won't be home to cook. Really enjoyed it.{ret}",
        "Out of town for work for a while. Loved the variety and seasoning.{ret}",
    ],
    LifeContext.NEW_ARRIVAL: [
        "Just had a baby and life is chaos right now, need to simplify. The recipes were great.{ret}",
        "Expecting a newborn soon and need to scale back for now. Loved the meals.{ret}",
    ],
    LifeContext.RELOCATION: [
        "Moving to a new city next month and not sure about delivery there. The food was delicious.{ret}",
        "Relocating for work, changing address soon. Really enjoyed the organic ingredients.{ret}",
        "In the middle of a move to a new apartment. Great recipes, will miss them.{ret}",
    ],
    LifeContext.OTHER: [
        "Going through some personal stuff right now and need to step back for now. Loved the meals.{ret}",
        "Some family circumstances mean I have to pause temporarily. The food was wonderful.{ret}",
    ],
}

RETURN_PHRASES = [
    " Hope to be back soon!",
    " Will resubscribe when things settle.",
    " I'll come back once I can.",
    " Looking forward to returning.",
]

LOW_TEMPLATES = [
    "Way too expensive for what you get. Not worth it.",
    "The recipes got really repetitive and boring after a while.",
    "Portions were small and the seasoning was bland. Disappointed.",
    "Overpriced compared to just buying groceries myself.",
    "Quality went downhill and I'm done with it. Never again.",
    "Too many ingredients to prep, more work than it's worth.",
    "Found a cheaper service that I like better.",
    "The meals just weren't very tasty. Cancelling for good.",
    "Packaging waste was excessive and it's not worth the price.",
    "Honestly just not impressed with the food quality.",
]

RELEASE_TEMPLATES = [
    "n/a",
    "none",
    "no comment",
    "cancel",
    "done",
    "stop",
    "-",
    "no",
    ".",
    "quit",
]


@dataclass
class GenConfig:
    n_records: int = 14231
    n_weeks: int = 8
    seed: int = 5905


def _weighted_choice(rng: random.Random, weights: dict) -> LifeContext:
    items = list(weights.items())
    total = sum(w for _, w in items)
    r = rng.uniform(0, total)
    upto = 0.0
    for ctx, w in items:
        upto += w
        if r <= upto:
            return ctx
    return items[-1][0]


def generate(config: GenConfig | None = None) -> list[dict]:
    """Generate a list of dummy cancellation records."""
    config = config or GenConfig()
    rng = random.Random(config.seed)
    rows: list[dict] = []

    for i in range(config.n_records):
        week = (i % config.n_weeks) + 1
        roll = rng.random()
        if roll < P_HIGH:
            ctx = _weighted_choice(rng, HIGH_CONTEXT_WEIGHTS)
            template = rng.choice(HIGH_TEMPLATES[ctx])
            ret = rng.random() < 0.62  # ~62% express explicit return intent
            comment = template.format(ret=(rng.choice(RETURN_PHRASES) if ret else ""))
        elif roll < P_HIGH + P_LOW:
            comment = rng.choice(LOW_TEMPLATES)
        else:
            comment = rng.choice(RELEASE_TEMPLATES)

        rows.append({
            "order_id": f"GC-{100000 + i}",
            "week": week,
            "comment": comment.strip(),
        })

    rng.shuffle(rows)
    return rows


def write_csv(path: str | Path, config: GenConfig | None = None) -> int:
    """Generate and write the dummy dataset to `path`. Returns the row count."""
    rows = generate(config)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["order_id", "week", "comment"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
