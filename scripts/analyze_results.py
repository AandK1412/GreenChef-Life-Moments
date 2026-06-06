#!/usr/bin/env python3
"""Summarise a classified output CSV and compare to the report's headline figures.

Prints recoverability mix, life-context distribution, priority bands, weekly
stability of the High-Potential segment, and the human-review rate. If
matplotlib is installed, also writes summary charts to data/figures/.

Usage:
    python scripts/analyze_results.py --in data/classified_output.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pct(n: int, total: int) -> str:
    return f"{100 * n / total:.2f}%" if total else "0.00%"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="inp", default=str(ROOT / "data" / "classified_output.csv"))
    parser.add_argument("--charts", action="store_true", help="also write charts (needs matplotlib)")
    args = parser.parse_args()

    inp = Path(args.inp)
    if not inp.exists():
        raise SystemExit(f"Not found: {inp}. Run scripts/run_classification.py first.")

    rows = load(inp)
    total = len(rows)

    rec = Counter(r["recoverability"] for r in rows)
    ctx = Counter(r["life_context"] for r in rows if r["recoverability"] == "High-Potential")
    bands = Counter(r["priority_band"] for r in rows)
    review = sum(1 for r in rows if r["needs_human_review"] == "True")
    sent = sum(1 for r in rows if r["sent_to_classifier"] == "True")
    used_llm = sum(1 for r in rows if r["used_llm"] == "True")

    weekly_high = defaultdict(int)
    weekly_total = defaultdict(int)
    for r in rows:
        w = int(r["week"])
        weekly_total[w] += 1
        if r["recoverability"] == "High-Potential":
            weekly_high[w] += 1

    high = rec.get("High-Potential", 0)

    print("=" * 64)
    print("GREEN CHEF LIFE MOMENTS - CLASSIFICATION SUMMARY")
    print("=" * 64)
    print(f"Total records:                 {total:,}")
    print()
    print("Recoverability mix            (report: High 21.86% / Low 68.02%)")
    for label in ("High-Potential", "Low-Potential", "Release"):
        print(f"  {label:<16} {rec.get(label, 0):>7,}   {pct(rec.get(label, 0), total)}")
    print()
    print("Priority bands")
    for label in ("Urgent", "High", "Moderate", "Low"):
        print(f"  {label:<16} {bands.get(label, 0):>7,}   {pct(bands.get(label, 0), total)}")
    print("  (report Urgent ~13.0% / 1,848 records)")
    print()
    print("High-Potential life-context distribution")
    for label, n in ctx.most_common():
        print(f"  {label:<16} {n:>7,}   {pct(n, high)}")
    print()
    print("Weekly High-Potential stability   (report range: 334-404)")
    highs = [weekly_high[w] for w in sorted(weekly_total)]
    for w in sorted(weekly_total):
        print(f"  Week {w}:  {weekly_high[w]:>5,} high  /  {weekly_total[w]:>5,} total")
    if highs:
        print(f"  range: {min(highs)}-{max(highs)}   mean: {sum(highs)/len(highs):.0f}/wk")
    print()
    print(f"Routed to human review:        {review:,}   ({pct(review, total)})")
    print(f"Passed pre-screen to classifier: {sent:,}   ({pct(sent, total)})")
    print(f"  -> pre-screen short-circuited  {total - sent:,}   ({pct(total - sent, total)}) with no AI call")
    print(f"Actual LLM API calls made:     {used_llm:,}   "
          f"(0 when running the offline heuristic backend)")
    print("=" * 64)

    if args.charts:
        _charts(rec, ctx, highs, sorted(weekly_total), weekly_total)


def _charts(rec, ctx, highs, weeks, weekly_total) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping charts.")
        return

    outdir = ROOT / "data" / "figures"
    outdir.mkdir(parents=True, exist_ok=True)

    # Recoverability mix.
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["High-Potential", "Low-Potential", "Release"]
    ax.bar(labels, [rec.get(x, 0) for x in labels], color=["#2e7d32", "#9e9e9e", "#cfd8dc"])
    ax.set_title("Recoverability Mix")
    ax.set_ylabel("Records")
    fig.tight_layout()
    fig.savefig(outdir / "recoverability_mix.png", dpi=120)
    plt.close(fig)

    # Weekly stability.
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(weeks, [weekly_total[w] for w in weeks], marker="o", label="Total cancellations")
    ax.plot(weeks, highs, marker="s", label="High-Potential")
    ax.set_title("Weekly Cancellations vs. High-Potential Segment")
    ax.set_xlabel("Week")
    ax.set_ylabel("Records")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / "weekly_stability.png", dpi=120)
    plt.close(fig)

    print(f"Charts written to {outdir}/")


if __name__ == "__main__":
    main()
