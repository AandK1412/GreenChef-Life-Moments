from collections import Counter

from life_moments.classifier import HeuristicClassifier
from life_moments.pipeline import Pipeline
from life_moments.synthetic import GenConfig, generate


def test_pipeline_single_record():
    pipe = Pipeline(classifier=HeuristicClassifier())
    rec = pipe.classify_record("GC-1", 1, "Traveling for work for two months, will be back!")
    assert rec.classification.recoverability.value == "High-Potential"
    assert rec.classification.life_context.value == "Work Travel"
    assert rec.track_name == "Work Travel"


def test_synthetic_distribution_matches_report():
    # Smaller sample for speed; proportions are seed-stable.
    rows = generate(GenConfig(n_records=4000, seed=5905))
    pipe = Pipeline(classifier=HeuristicClassifier())
    mix = Counter(r.classification.recoverability.value for r in pipe.run(rows))
    total = sum(mix.values())

    high = mix["High-Potential"] / total
    low = mix["Low-Potential"] / total

    # Report: High 21.86%, Low 68.02%. Allow tolerance for sampling + classifier noise.
    assert 0.17 <= high <= 0.27, f"High-Potential share {high:.3f} out of expected band"
    assert 0.60 <= low <= 0.74, f"Low-Potential share {low:.3f} out of expected band"


def test_pipeline_never_raises_on_messy_input():
    pipe = Pipeline(classifier=HeuristicClassifier())
    for junk in ["", "   ", "?!?", "n/a", "MONEY MONEY MONEY", "love"]:
        rec = pipe.classify_record("x", 1, junk)
        assert rec.classification.priority_score >= 0
