from life_moments.routing import route
from life_moments.schemas import Classification


def test_high_potential_budget_routes_to_budget_track():
    c = Classification(recoverability="High-Potential", life_context="Budget Pressure",
                       sentiment="Positive", priority_score=88, confidence=0.9)
    d = route(c)
    assert d.track_name == "Budget Pressure"
    assert "discount" in d.primary_offer.lower()
    assert d.outreach_sla == "Within 24 hours"  # urgent band


def test_low_potential_routes_to_standard_workflow():
    c = Classification(recoverability="Low-Potential", life_context="None",
                       sentiment="Negative", priority_score=5, confidence=0.9)
    d = route(c)
    assert d.track_name == "Standard Cancellation Workflow"
    assert d.outreach_sla == "None"


def test_release_routes_to_standard_workflow():
    c = Classification(recoverability="Release", priority_score=0, confidence=0.9)
    assert route(c).track_name == "Standard Cancellation Workflow"


def test_high_band_sla_is_48_72h():
    c = Classification(recoverability="High-Potential", life_context="Work Travel",
                       sentiment="Neutral", priority_score=60, confidence=0.9)
    assert route(c).outreach_sla == "Within 48-72 hours"
