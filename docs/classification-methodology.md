# Classification Methodology

This document describes the labelling scheme the system applies to each
cancellation comment. It corresponds to **Appendix G** of the capstone report.

## Outputs

Each comment receives three outputs plus supporting metadata:

| Output | Values |
|---|---|
| **Recoverability class** | `High-Potential` · `Low-Potential` · `Release` |
| **Life-context category** | `Budget Pressure` · `Schedule Change` · `Health Event` · `Work Travel` · `New Arrival` · `Relocation` · `Other` · `None` |
| **Priority intervention score** | integer `0–100` |
| sentiment | `Positive` · `Neutral` · `Negative` |
| return_intent | boolean |
| confidence | float `0.0–1.0` |
| evidence | a verbatim span from the comment |

## The four-dimensional recoverability rubric

A subscriber is **recoverable** when their exit is temporary and externally
driven rather than a verdict on the product. The classifier reasons over four
dimensions:

1. **Temporariness** — is the departure reason likely to resolve within ~12 weeks?
2. **Externality** — is the cause a life circumstance, not product dissatisfaction?
3. **Emotional tone** — positive/neutral vs. negative sentiment toward the brand.
4. **Relationship quality** — did the comment suggest the subscriber valued the product?

| Class | Meaning | Action |
|---|---|---|
| **High-Potential** | Temporary, external, neutral/positive | Personalized retention track |
| **Low-Potential** | Product dissatisfaction (price, taste, fit) | Standard workflow |
| **Release** | Insufficient signal to classify | Warm farewell, no offer |

## The core diagnostic: sentiment divergence (Section V.4)

The single most important insight is that **two subscribers can cite the same
exit reason and have opposite recoverability**. A *Budget Pressure* cancellation
from a subscriber who writes "I love these meals but money is tight right now" is
a product endorsement constrained by circumstance — recoverable with a temporary
accommodation. The same "budget" reason with negative sentiment ("overpriced, not
worth it") is a permanent value objection — not recoverable by a discount.

The system therefore never routes on exit reason alone. **Sentiment is what
separates recoverable from unrecoverable within a category.**

## Priority intervention score

The 0–100 score combines positive brand sentiment, an explicit life-context
signal, and expressed intent to return. It drives the urgency triage:

| Band | Score | SLA |
|---|---|---|
| Urgent | 75–100 | Outreach within 24h, CRM-flagged for personalization |
| High | 50–74 | Automated outreach within 48–72h |
| Moderate | 25–49 | Scheduled re-engagement sequence |
| Low | 0–24 | Scheduled re-engagement sequence |

## Heuristic vs. LLM scoring

The offline `HeuristicClassifier` approximates the rubric with keyword matching:

- life-context vocabulary → category;
- positive/negative cue counts → sentiment;
- `context present AND sentiment not negative` → High-Potential;
- score = sentiment weight + context bonus + return-intent bonus + anchor bonus.

This is deliberately simple and transparent. It reproduces the report's headline
distribution on the synthetic data but, as the report notes, **multi-part
reasoning (especially the sentiment-divergence judgment) is why the production
system uses an LLM** — the heuristic predictably stumbles on idiomatic cases
(e.g. "moving on" is not relocation), which is exactly the kind of case the
regression suite tolerates within its error budget.

## Validation (anti-hallucination)

Before any classification is acted on, four code-level checks run
(`validation.py`):

1. **Format** — output parses into the typed schema.
2. **Validity** — enum values valid, score in range, no `High-Potential` + `None`.
3. **Confidence** — outputs below `0.6` are routed to human review.
4. **Evidence grounding** — the cited evidence span must literally appear in the
   comment; if not, the record is flagged as a possible hallucination.

## Validation against human labels (Appendix G.2)

The report validated the methodology against a 20% manually-reviewed sample and
reported **88.2% overall agreement** (High-Potential 83.1%, Low-Potential 89.4%,
Release 91.2%), exceeding the 80% Phase-1 exit gate. The repository's regression
suite (`tests/test_regression.py`) enforces the analogous deployment gate: a
prompt/instruction change may ship only if it misclassifies at most **3 of 50**
known cases.
