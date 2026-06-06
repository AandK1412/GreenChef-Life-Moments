import pytest
from pydantic import ValidationError

from life_moments.classifier import parse_classification
from life_moments.config import PriorityBand, RecoverabilityClass
from life_moments.schemas import Classification


def test_priority_score_bounds_enforced():
    with pytest.raises(ValidationError):
        Classification(recoverability="Release", priority_score=150, confidence=0.5)


def test_confidence_bounds_enforced():
    with pytest.raises(ValidationError):
        Classification(recoverability="Release", priority_score=10, confidence=1.5)


def test_band_property():
    c = Classification(recoverability="High-Potential", priority_score=88, confidence=0.9)
    assert c.band is PriorityBand.URGENT


def test_parse_classification_with_fences():
    raw = '```json\n{"recoverability": "Release", "priority_score": 0, "confidence": 0.9}\n```'
    c = parse_classification(raw)
    assert c.recoverability is RecoverabilityClass.RELEASE


def test_parse_classification_with_preamble():
    raw = 'Here is the result: {"recoverability":"Low-Potential","priority_score":5,"confidence":0.8}'
    c = parse_classification(raw)
    assert c.recoverability is RecoverabilityClass.LOW_POTENTIAL
