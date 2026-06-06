from life_moments.config import LifeContext, RecoverabilityClass
from life_moments.prescreen import pre_screen


def test_short_comment_short_circuits_to_release():
    result = pre_screen("n/a")
    assert result.send_to_llm is False
    assert result.shortcut.recoverability is RecoverabilityClass.RELEASE


def test_no_context_complaint_short_circuits_to_low():
    result = pre_screen("Way too expensive and the recipes are repetitive.")
    assert result.send_to_llm is False
    assert result.shortcut.recoverability is RecoverabilityClass.LOW_POTENTIAL


def test_life_context_comment_is_sent_to_llm():
    result = pre_screen("Money is really tight right now but I love the meals.")
    assert result.send_to_llm is True
    assert LifeContext.BUDGET_PRESSURE in result.matched_contexts


def test_empty_comment_is_release():
    assert pre_screen("").shortcut.recoverability is RecoverabilityClass.RELEASE
