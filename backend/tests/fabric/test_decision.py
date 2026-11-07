"""The ResNet50 + NASNet decision rule."""

import pytest

from backend.app.fabric import decision as d
from backend.app.fabric.decision import Prediction, decide

T = 0.60


def P(model, label, conf):
    return Prediction(model=model, label=label, confidence=conf, top_k=((label, conf),))


def test_agreement_both_confident():
    r = decide([P("resnet50", "denim", 0.91), P("nasnet", "denim", 0.74)], T)
    assert r.status == d.AGREEMENT
    assert r.final_label == "denim"
    assert r.candidates == ("denim",)
    assert not r.low_confidence


def test_weak_agreement_when_one_below_threshold():
    r = decide([P("resnet50", "tshirt", 0.95), P("nasnet", "tshirt", 0.41)], T)
    assert r.status == d.WEAK_AGREEMENT
    assert r.final_label == "tshirt"
    assert r.low_confidence


def test_disagreement_asserts_no_label_and_reports_both():
    r = decide([P("resnet50", "denim", 0.99), P("nasnet", "shirt", 0.99)], T)
    assert r.status == d.DISAGREEMENT
    assert r.final_label is None
    assert r.candidates == ("denim", "shirt")
    assert "disagree" in r.summary.lower()


def test_high_confidence_does_not_override_disagreement():
    # Confidence must never be used to break a tie between models.
    r = decide([P("resnet50", "denim", 0.999), P("nasnet", "shirt", 0.61)], T)
    assert r.final_label is None


def test_single_model_confident():
    r = decide([P("nasnet", "towel", 0.88)], T)
    assert r.status == d.SINGLE_MODEL
    assert r.final_label == "towel"
    assert "could not be cross-checked" in r.summary


def test_single_model_below_threshold_is_uncertain():
    r = decide([P("resnet50", "towel", 0.40)], T)
    assert r.status == d.UNCERTAIN
    assert r.final_label is None
    assert r.candidates == ("towel",)
    assert r.low_confidence


def test_requires_a_prediction():
    with pytest.raises(ValueError):
        decide([], T)


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_threshold_validated(bad):
    with pytest.raises(ValueError):
        decide([P("resnet50", "x", 0.9)], bad)


def test_confidence_scores_are_not_averaged_or_combined():
    r = decide([P("resnet50", "denim", 0.9), P("nasnet", "denim", 0.7)], T)
    # The decision exposes no combined score at all.
    assert not hasattr(r, "confidence")
    assert not hasattr(r, "score")