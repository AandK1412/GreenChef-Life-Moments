#!/usr/bin/env python3
"""Generate the structurally-representative synthetic cancellation dataset.

Usage:
    python scripts/generate_data.py [--rows 14231] [--out data/synthetic_cancellations.csv]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from life_moments.synthetic import GenConfig, write_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=14231, help="number of records")
    parser.add_argument("--weeks", type=int, default=8, help="number of weeks")
    parser.add_argument("--seed", type=int, default=5905, help="random seed")
    parser.add_argument(
        "--out",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "data" / "synthetic_cancellations.csv"),
    )
    args = parser.parse_args()

    n = write_csv(args.out, GenConfig(n_records=args.rows, n_weeks=args.weeks, seed=args.seed))
    print(f"Wrote {n:,} synthetic cancellation records to {args.out}")


if __name__ == "__main__":
    main()
