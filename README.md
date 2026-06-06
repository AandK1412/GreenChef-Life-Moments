<div align="center">

# 🌱 Green Chef Life Moments

### AI-assisted subscriber-retention classification

**Intercept recoverable churn at the moment of cancellation — by separating
subscribers leaving for *temporary life reasons* from those leaving over
*permanent product dissatisfaction*.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-25%20passing-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Backend](https://img.shields.io/badge/LLM-Claude%20Sonnet%204.6-8A2BE2.svg)](#backends)
[![Runs offline](https://img.shields.io/badge/runs%20offline-no%20API%20key%20needed-orange.svg)](#quickstart)

</div>

---

## What this is

A reference implementation of the **Green Chef Life Moments** retention system —
the capstone project for **MGT 5905**, the MSBA-GBA program at Virginia Tech's
Pamplin College of Business.

The analysis behind it found that **21.86% of Green Chef cancellations** (~3,111
subscribers per quarter) are driven by **temporary life disruptions** — budget
pressure, a schedule change, work travel, a health event, a new baby, a move —
not by dissatisfaction. These subscribers leave with *positive* brand sentiment
and get the same generic exit flow as everyone else. That is recoverable revenue
walking out the door.

This system reads each cancellation comment, decides how recoverable the
subscriber is and why they're leaving, and routes High-Potential subscribers to a
**personalized retention track** calibrated to their specific life context — all
on existing infrastructure, with no new product to build.

> 📄 **The full capstone report** is in [`docs/capstone-report.md`](docs/capstone-report.md)
> (original Word doc: [`docs/MGT5905_Report_Final.docx`](docs/MGT5905_Report_Final.docx)).

---

## The core idea: sentiment divergence

Two subscribers cite the *same* reason and have *opposite* recoverability:

| Comment | Reason | Sentiment | Class | Response |
|---|---|---|---|---|
| "I **love** these meals but money's tight right now" | Budget Pressure | Positive | **High-Potential** | Temporary discount / smaller box |
| "Way **overpriced**, not worth it" | (price) | Negative | **Low-Potential** | Standard workflow |

Exit reason alone is misleading. **Sentiment is the diagnostic.** That judgment —
not keyword matching — is why the production system uses an LLM.

---

## How it works

```
cancellation comment
        │
        ▼
┌───────────────┐   no life-context signal / too short
│  1. PRE-SCREEN│ ───────────────────────────────────────►  short-circuit (no AI call)
│  keyword filter│                                            ~78% of comments
└───────┬───────┘
        │ has signal
        ▼
┌───────────────┐
│  2. CLASSIFY  │   Claude Sonnet 4.6 (Batch API)  ── or ──  offline heuristic
│               │   → recoverability · life-context · sentiment · priority 0–100 · evidence
└───────┬───────┘
        ▼
┌───────────────┐   confidence < 0.6  OR  evidence not in comment
│  3. VALIDATE  │ ───────────────────────────────────────►  human-review queue
│  4 checks     │
└───────┬───────┘
        ▼
┌───────────────┐   High-Potential → personalized track (offer + SLA)
│  4. ROUTE     │   Low / Release  → standard cancellation workflow
└───────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full design.

---

## Quickstart

No API key required — the pipeline ships with an offline heuristic backend so the
whole thing runs end-to-end out of the box.

```bash
git clone <your-fork-url> green-chef-life-moments
cd green-chef-life-moments
pip install -r requirements.txt

# 1. generate the synthetic dataset (14,231 dummy cancellations)
python scripts/generate_data.py

# 2. classify + route every record
python scripts/run_classification.py

# 3. summarise the results
python scripts/analyze_results.py --charts
```

…or just `make demo`.

### Example summary output

```
Recoverability mix            (report: High 21.86% / Low 68.02%)
  High-Potential     3,096   21.76%
  Low-Potential      9,650   67.81%
  Release            1,485   10.43%

Priority bands
  Urgent             1,897   13.33%     (report Urgent ~13.0% / 1,848)

High-Potential life-context distribution
  Budget Pressure    1,752   56.59%
  Schedule Change      531   17.15%
  ...

Weekly High-Potential stability   (report range: 334-404)
  range: 369-408   mean: 387/wk

Passed pre-screen to classifier: 3,096   (21.76%)
  -> pre-screen short-circuited  11,135   (78.24%) with no AI call
```

The synthetic data reproduces the report's headline figures within sampling
tolerance.

---

## Use it as a library

```python
from life_moments import Pipeline

pipe = Pipeline()  # auto-selects Claude backend if ANTHROPIC_API_KEY is set
record = pipe.classify_record(
    order_id="GC-100001", week=3,
    comment="Traveling for work for the next two months — will resubscribe when I'm back!",
)

print(record.classification.recoverability.value)  # High-Potential
print(record.classification.life_context.value)    # Work Travel
print(record.track_name, "→", record.primary_offer)
# Work Travel → Flexible pause or delivery-skip for stated travel period
print(record.outreach_sla)                          # Within 48-72 hours
```

---

## Backends

| Backend | When | Notes |
|---|---|---|
| **`anthropic`** | `ANTHROPIC_API_KEY` set + `anthropic` installed | **Claude Sonnet 4.6** via the Appendix-M prompt, with **prompt caching** and **Batch API** for bulk jobs. **Opus 4.6** reserved for human-review escalations. |
| **`heuristic`** | default fallback | Deterministic rule engine — no key, no network. Powers tests/CI and serves as a transparent baseline. |

Enable Claude:

```bash
cp .env.example .env       # add your key
export ANTHROPIC_API_KEY=sk-...
python scripts/run_classification.py    # backend auto-switches to Claude
```

Cost is low by design: pre-screen filtering + prompt caching + Batch API put the
report's projected annual AI spend at **$300–$800**.

---

## Retention tracks (Table VII-1)

| Life context | Primary offer |
|---|---|
| Budget Pressure | Temporary 10–20% discount or smaller box for 4 weeks |
| Schedule Change | Extended pause (4–8 weeks) at no penalty |
| Health Event | Free plan switch to relevant dietary tier + empathetic message |
| Work Travel | Flexible pause / delivery-skip for the travel period |
| New Arrival | Simplified meal tier; frequency adjustment |
| Relocation | Coverage confirmation for new address; welcome offer |

Every offer is an **existing** Green Chef accommodation — the system routes, it
doesn't invent new product.

---

## The business case (Section VIII)

| Metric | Value |
|---|---|
| One-time implementation | ~$175K ($124K–$207K) |
| Payback period | **≈ 3.6 months** |
| 3-year NPV (10%) | **≈ $1.29M** |
| 3-year ROI | **639%** |

Re-derive it yourself — the model is auditable code:

```bash
python -m life_moments.economics
# {"annual_profit_contribution": 616005, "payback_months": 3.6, "npv": 1294742, "roi_pct": 639}
```

Details and assumptions: [`docs/economic-model.md`](docs/economic-model.md).

---

## Project layout

```
green-chef-life-moments/
├── README.md
├── pyproject.toml · requirements*.txt · Makefile · LICENSE · .env.example
├── docs/
│   ├── capstone-report.md          # full report (Markdown)
│   ├── MGT5905_Report_Final.docx   # original Word doc
│   ├── architecture.md
│   ├── classification-methodology.md
│   └── economic-model.md
├── data/
│   ├── README.md                   # data-governance note (synthetic only)
│   └── synthetic_cancellations.csv # generated
├── src/life_moments/
│   ├── config.py · schemas.py · prescreen.py · prompts.py
│   ├── classifier.py · validation.py · routing.py · pipeline.py
│   ├── synthetic.py · economics.py
├── scripts/
│   ├── generate_data.py · run_classification.py · analyze_results.py
└── tests/                          # 25 tests incl. the 50-case regression gate
```

---

## Testing

```bash
pip install -r requirements-dev.txt
make test
```

The suite covers the pre-screen, schemas/parsing, the four validation checks,
routing, the end-to-end pipeline (asserting the report's distribution on
synthetic data), the economic model, and the **regression gate** — the report's
rule that a classification change may ship only if it misses **≤ 3 of 50** golden
cases (`tests/fixtures/regression_cases.json`).

---

## Methodology & validation

The classification approach is documented in
[`docs/classification-methodology.md`](docs/classification-methodology.md). In the
report, the methodology was validated against a 20% manually-reviewed sample at
**88.2% agreement**, clearing the 80% Phase-1 quality gate.

---

## Team

· Vignesh Anand · Yash Mahadik · Anrunya Patole · Kshama Purohit , MSBA-GBA Capstone 
· Pamplin College of Business, Virginia Tech,Faculty Advisor: Prof. Sean Raines 
· Sponsor: Green Chef / HelloFresh SE

---

## Disclaimer

This is academic capstone work. All conclusions and recommendations are those of
the student project team and **do not represent the official views or positions
of HelloFresh SE or Virginia Tech**. The repository contains **synthetic data
only**; no real subscriber data is used or reproduced. "Green Chef", "HelloFresh",
and competitor names are referenced for academic analysis and belong to their
respective owners.

Licensed under the [MIT License](LICENSE).
#
