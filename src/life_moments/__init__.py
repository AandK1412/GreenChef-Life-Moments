"""Green Chef Life Moments — AI-assisted subscriber-retention classification.

Reference implementation of the system described in the Virginia Tech MSBA-GBA
capstone report (MGT 5905). See docs/capstone-report.md.
"""

from __future__ import annotations

from .classifier import (
    AnthropicClassifier,
    HeuristicClassifier,
    get_classifier,
    parse_classification,
)
from .config import (
    LifeContext,
    PriorityBand,
    RecoverabilityClass,
    Sentiment,
    Settings,
    priority_band,
)
from .economics import BASELINE, Scenario, npv, payback_years, roi, summary
from .pipeline import Pipeline
from .prescreen import pre_screen
from .routing import route
from .schemas import Classification, RoutedRecord
from .validation import validate

__all__ = [
    "Pipeline",
    "Classification",
    "RoutedRecord",
    "get_classifier",
    "HeuristicClassifier",
    "AnthropicClassifier",
    "parse_classification",
    "pre_screen",
    "route",
    "validate",
    "RecoverabilityClass",
    "LifeContext",
    "Sentiment",
    "PriorityBand",
    "Settings",
    "priority_band",
    "Scenario",
    "BASELINE",
    "npv",
    "roi",
    "payback_years",
    "summary",
]

__version__ = "1.0.0"
