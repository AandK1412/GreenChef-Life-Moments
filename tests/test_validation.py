from life_moments.schemas import Classification
from life_moments.validation import validate


def _c(**kw):
    base = dict(recoverability="High-Potential", life_context="Budget Pressure",
                sentiment="Positive", priority_score=80, confidence=0.9)
    base.update(kw)
    return Classification(**base)


def test_valid_classification_passes():
    comment = "Money is tight but I love it, hope to be back."
    result = validate(_c(evidence="Money is tight"), comment)
    assert result.ok is True
    assert result.needs_human_review is False


def test_low_confidence_flags_review():
    result = validate(_c(confidence=0.4), "Money is tight")
    assert result.needs_human_review is True
    assert any("confidence" in r for r in result.reasons)


def test_hallucinated_evidence_flags_review():
    result = validate(_c(evidence="I won the lottery"), "Money is tight right now")
    assert result.needs_human_review is True
    assert any("evidence" in r for r in result.reasons)


def test_high_potential_without_context_flags_review():
    result = validate(
        _c(life_context="None"),
        "Some comment with enough length here",
    )
    assert result.needs_human_review is True
