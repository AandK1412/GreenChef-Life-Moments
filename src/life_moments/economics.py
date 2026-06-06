"""Economic model (Section VIII) — a small, auditable calculator.

Reproduces the report's payback / NPV / ROI under a configurable scenario.
Dependency-free so the headline business case can be re-derived and stress-tested.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    weekly_cancellations: int = 7500
    life_context_share: float = 0.26
    conversion_rate: float = 0.10
    retention_weeks: int = 6
    aov: float = 75.0
    aebitda_margin: float = 0.135
    implementation_cost: float = 175_000.0
    annual_operating_cost: float = 25_000.0
    discount_rate: float = 0.10
    horizon_years: int = 3


BASELINE = Scenario()


def annual_profit_contribution(s: Scenario) -> float:
    addressable = s.weekly_cancellations * s.life_context_share
    retained_per_week = addressable * s.conversion_rate
    additional_active = retained_per_week * s.retention_weeks
    weekly_revenue = additional_active * s.aov
    annual_revenue = weekly_revenue * 52
    return annual_revenue * s.aebitda_margin


def net_cash_flows(s: Scenario) -> list[float]:
    """FY0..FYn net cash flows."""
    contribution = annual_profit_contribution(s)
    flows = [-s.implementation_cost]
    for _ in range(s.horizon_years):
        flows.append(contribution - s.annual_operating_cost)
    return flows


def npv(s: Scenario) -> float:
    return sum(cf / (1 + s.discount_rate) ** t for t, cf in enumerate(net_cash_flows(s)))


def payback_years(s: Scenario) -> float:
    annual_net = annual_profit_contribution(s) - s.annual_operating_cost
    return s.implementation_cost / annual_net


def roi(s: Scenario) -> float:
    total_cost = s.implementation_cost + s.annual_operating_cost * s.horizon_years
    gross = annual_profit_contribution(s) * s.horizon_years
    return (gross - total_cost) / total_cost


def summary(s: Scenario = BASELINE) -> dict:
    return {
        "annual_profit_contribution": round(annual_profit_contribution(s)),
        "net_cash_flows": [round(x) for x in net_cash_flows(s)],
        "payback_years": round(payback_years(s), 3),
        "payback_months": round(payback_years(s) * 12, 1),
        "npv": round(npv(s)),
        "roi_pct": round(roi(s) * 100),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(summary(), indent=2))
