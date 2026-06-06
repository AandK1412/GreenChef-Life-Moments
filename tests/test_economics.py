from life_moments.economics import BASELINE, npv, payback_years, roi, summary


def test_baseline_matches_report():
    s = summary(BASELINE)
    assert s["annual_profit_contribution"] == 616005
    assert s["net_cash_flows"] == [-175000, 591005, 591005, 591005]
    assert s["payback_months"] == 3.6
    assert abs(s["npv"] - 1_294_742) <= 5
    assert s["roi_pct"] == 639


def test_npv_positive_under_baseline():
    assert npv(BASELINE) > 0


def test_payback_under_a_year():
    assert payback_years(BASELINE) < 1.0


def test_roi_is_a_ratio():
    assert roi(BASELINE) > 0
