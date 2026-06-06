# System Architecture

The Life Moments system is a thin decision layer that sits on top of HelloFresh's
existing subscriber-management, CRM, and messaging infrastructure. It introduces
no new product capabilities — it routes already-existing accommodations (pauses,
discounts, plan switches, box-size changes) to the subscribers who match them.

This repository implements the **classification and routing core** of that layer.

## Pipeline

Every cancellation comment flows through four stages:

```
                                  ┌─────────────────────────────────────────┐
  cancellation event              │           Life Moments core              │
  (order_id, week, comment) ────► │                                          │
                                  │  1. PRE-SCREEN   prescreen.py             │
                                  │     keyword filter; ~74-78% of comments   │
                                  │     short-circuit here with no AI call    │
                                  │              │                            │
                                  │              ▼ (has life-context signal)  │
                                  │  2. CLASSIFY    classifier.py             │
                                  │     Claude Sonnet 4.6 (Batch API)         │
                                  │     │ or offline heuristic backend        │
                                  │     ▼                                     │
                                  │     Classification {recoverability,       │
                                  │       life_context, sentiment, priority,  │
                                  │       confidence, evidence, return_intent}│
                                  │              │                            │
                                  │              ▼                            │
                                  │  3. VALIDATE    validation.py             │
                                  │     format · validity · confidence≥0.6 ·  │
                                  │     evidence grounding (anti-hallucination)│
                                  │              │                            │
                                  │       ┌──────┴───────┐                    │
                                  │       ▼              ▼                    │
                                  │   human review     4. ROUTE  routing.py   │
                                  │   (CRM queue)      track + offer + SLA     │
                                  └─────────────────────────────────────────┘
                                                  │
                                                  ▼
                              High-Potential → personalized outreach track
                              Low-Potential / Release → standard cancellation flow
```

## Module map

| Module | Responsibility | Report reference |
|---|---|---|
| `config.py` | Enums, thresholds, model names, life-context vocabulary, settings | Appendix B, G, M |
| `schemas.py` | Typed classification contract + enriched output record | Appendix G.1 |
| `prescreen.py` | Cheap keyword filter; short-circuits no-signal comments | Section IX.1 |
| `prompts.py` | Cacheable instruction template + few-shot anchors | Appendix M |
| `classifier.py` | Anthropic + heuristic backends behind one interface | Section VII.2 (Capability 1) |
| `validation.py` | The four code-level output checks | Section IX.3 |
| `routing.py` | Response tracks (Table VII-1) + priority triage | Section VII.2-VII.3 |
| `pipeline.py` | Orchestrates the four stages over records | Section V.1 |
| `synthetic.py` | Generates structurally-representative dummy data | Appendix H |

## Backends

The classifier is backend-agnostic. Two implementations satisfy the same
interface:

- **`AnthropicClassifier`** — the production path. Sends the Appendix-M prompt to
  Claude with **prompt caching** on the constant instruction block and, for bulk
  jobs, the **Batch API** (50% cheaper). The report recommends **Claude Sonnet
  4.6** for routine classification and reserves **Claude Opus 4.6** for cases
  escalated to human review.
- **`HeuristicClassifier`** — a deterministic, dependency-free rule engine that
  produces the same schema offline. It powers the demo, the tests, and CI with no
  API key, and serves as a transparent baseline against which the LLM can be
  compared.

`get_classifier()` chooses automatically: it uses the Anthropic backend when an
API key and the `anthropic` package are present, otherwise the heuristic one.

## Cost-control design (Section IX.1)

The architecture encodes five cost principles directly:

1. **Filter before classifying** — the pre-screen removes the majority of
   comments before any AI call.
2. **Batch where possible** — bulk/overnight processing uses the Batch API.
3. **Cache the instruction template** — the constant system prompt is marked
   cacheable.
4. **Enforce safety in code** — validation runs in code, not in the prompt.
5. **Test silently first** — Phase 1 runs in shadow mode; this repo's pipeline
   produces outputs without triggering any outreach.

## Safety & privacy posture

- **No live action.** This core only labels and routes; it does not send
  messages. Outreach is a downstream CRM concern (shadow-mode safe by default).
- **PII handling.** In production, names/PII are removed before transmission
  (NER + pattern matching, Section IX.3). The synthetic data here contains no
  real subscriber information.
- **Evidence grounding.** The validation layer rejects classifications whose
  cited evidence span is absent from the comment, catching hallucinations.
