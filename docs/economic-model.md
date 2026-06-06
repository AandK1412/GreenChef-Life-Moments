# Economic Model

This summarises **Section VIII** of the capstone report. All figures are
scenario-based and presented as a directional framework, not a definitive
business case. Figures not sourced from public domains are working estimates.

## Headline results (conservative scenario)

| Metric | Value |
|---|---|
| One-time implementation cost | **$175,000** (range $124K–$207K) |
| Annual operating cost | **$25,000** (range $19.3K–$41.8K) |
| Payback period | **≈ 3.6 months** |
| 3-year NPV (10% discount) | **≈ $1.29 million** |
| 3-year ROI | **639%** (≈ $7.39 returned per $1 invested) |

## Key assumptions (Table VIII-1)

| Assumption | Value | Basis |
|---|---|---|
| Active Green Chef subscriber base | 100,000 | Q1 2026 data midpoint (estimate) |
| Average weekly order value (AOV) | $75 | Proxy from HF Group €66.5 AOV |
| Weekly cancellation rate | 7.5% | Q1 2026 dataset midpoint |
| Life-context segment share | 26% | 16% Intent + 10% other life-context |
| Intervention conversion rate | 10% | Working estimate |
| Additional weeks retained | 6 | Working estimate |
| Meal-kit AEBITDA margin | 13.5% | HelloFresh FY 2025 public results |
| NPV discount rate | 10% | Standard software-investment hurdle |

## The derivation chain (Section VIII.2)

```
7,500 weekly cancellations
  × 26%  life-context segment        = 1,950 addressable / week
  × 10%  conversion                  =   195 retained / week
  × 6    weeks retention extension   = 1,170 additional active subscribers
  × $75  AOV                         = $87,750 incremental weekly revenue
  × 52   weeks                       = $4,563,000 incremental annual revenue
  × 13.5% AEBITDA margin             = $616,005 annual profit contribution
```

## Three-year cash flow (Table VIII-2)

| Item | FY 0 | FY 1 | FY 2 | FY 3 |
|---|---|---|---|---|
| Implementation | −$175,000 | — | — | — |
| Operating costs | — | −$25,000 | −$25,000 | −$25,000 |
| AEBITDA contribution | — | +$616,005 | +$616,005 | +$616,005 |
| **Net cash flow** | **−$175,000** | **+$591,005** | **+$591,005** | **+$591,005** |
| Cumulative | −$175,000 | +$416,005 | +$1,007,010 | +$1,598,015 |

## Reproduce it

A small, dependency-free calculator is included so the numbers are auditable:

```bash
python -c "import sys; sys.path.insert(0,'src'); from life_moments.economics import summary, BASELINE; print(summary(BASELINE))"
```

## Limitations (Section VIII.4)

- Implementation cost is the team's estimate, not validated against HelloFresh's
  internal engineering rates.
- The 26% addressable-segment figure derives from structurally representative
  dummy data and manual review; actuals vary by quarter.
- FY 1–3 benefits are modelled as constant and do not account for competitive
  dynamics that may erode the differentiation value of Life Moments over time.

> The AI API cost itself is small: after pre-screen filtering, prompt caching,
> and Batch API usage, the report estimates **$300–$800/year** at projected
> volume — a rounding error against the retained-revenue contribution.
