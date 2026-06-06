"""Regression suite gate (Appendix M).

The report specifies a suite of 50 known cases run whenever the classification
instructions change; if more than 3 of 50 are wrong, the change is blocked.
This test enforces exactly that gate against the active classifier backend.
"""

import json
from pathlib import Path

from life_moments.classifier import HeuristicClassifier

FIXTURE = Path(__file__).parent / "fixtures" / "regression_cases.json"
MAX_ALLOWED_ERRORS = 3


def _load_cases():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data["cases"]


def test_regression_suite_within_gate():
    clf = HeuristicClassifier()
    cases = _load_cases()
    assert len(cases) == 50, "regression suite must contain exactly 50 cases"

    errors = []
    for case in cases:
        # Mirror the pipeline: short / no-context comments are resolved by the
        # pre-screen, so route everything through it for a faithful gate.
        from life_moments.prescreen import pre_screen

        screen = pre_screen(case["comment"])
        result = screen.shortcut if not screen.send_to_llm else clf.classify(case["comment"])
        if result.recoverability.value != case["recoverability"]:
            errors.append((case["comment"], case["recoverability"], result.recoverability.value))

    assert len(errors) <= MAX_ALLOWED_ERRORS, (
        f"{len(errors)} of {len(cases)} cases wrong (gate allows {MAX_ALLOWED_ERRORS}):\n"
        + "\n".join(f"  {c!r}: expected {exp}, got {got}" for c, exp, got in errors)
    )
