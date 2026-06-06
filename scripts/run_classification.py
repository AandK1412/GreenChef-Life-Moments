#!/usr/bin/env python3
"""Run the Life Moments classification pipeline over a CSV of cancellations.

Input CSV must have columns: order_id, week, comment.
Output CSV adds the classification, routing decision, and review flag.

Usage:
    python scripts/run_classification.py \
        --in data/synthetic_cancellations.csv \
        --out data/classified_output.csv

Backend selection (env vars):
    LIFE_MOMENTS_BACKEND = auto | anthropic | heuristic   (default: auto)
    ANTHROPIC_API_KEY    = <key>   (enables the Claude backend under "auto")
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from life_moments.pipeline import Pipeline  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIELDNAMES = [
    "order_id", "week", "comment", "recoverability", "life_context",
    "sentiment", "priority_score", "priority_band", "return_intent",
    "confidence", "evidence", "track_name", "primary_offer",
    "secondary_action", "outreach_sla", "channel", "needs_human_review",
    "review_reason", "sent_to_classifier", "used_llm",
]


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="inp", default=str(ROOT / "data" / "synthetic_cancellations.csv"))
    parser.add_argument("--out", dest="out", default=str(ROOT / "data" / "classified_output.csv"))
    parser.add_argument("--limit", type=int, default=0, help="process only the first N rows (0 = all)")
    args = parser.parse_args()

    inp, out = Path(args.inp), Path(args.out)
    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}. Run scripts/generate_data.py first.")

    pipeline = Pipeline()
    print(f"Backend: {pipeline.classifier.name}")

    rows = list(read_rows(inp))
    if args.limit:
        rows = rows[: args.limit]

    start = time.time()
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for record in pipeline.run(rows):
            writer.writerow(record.flat())
            n += 1
            if n % 2000 == 0:
                print(f"  classified {n:,} / {len(rows):,}")

    elapsed = time.time() - start
    print(f"Classified {n:,} records in {elapsed:.1f}s -> {out}")


if __name__ == "__main__":
    main()
