"""Impact estimates: weights, aggregation, and honesty about unverified factors."""

import pytest

from backend.app.fabric import impact


def test_user_weight_wins():
    assert impact.resolve_weight("denim", 0.9) == (0.9, impact.WEIGHT_USER)


@pytest.mark.parametrize("bad", [0, -1, 999, "abc", None])
def test_invalid_user_weight_falls_back_to_category(bad):
    w, src = impact.resolve_weight("denim", bad)
    assert src == impact.WEIGHT_CATEGORY and w == 0.70


def test_unknown_category_uses_default_weight():
    assert impact.resolve_weight("spaceship") == (0.30, impact.WEIGHT_DEFAULT)
    assert impact.resolve_weight(None) == (0.30, impact.WEIGHT_DEFAULT)


def test_summary_counts_only_completed_projects_as_reuse():
    s = impact.summarize(analyses_count=5, saved_ideas_count=3, projects=[])
    assert s["analyses_count"] == 5 and s["saved_ideas_count"] == 3
    assert s["garments_reused_estimate"] == 0
    assert s["fabric_kg_diverted_upper_bound"] == 0


def test_summary_sums_and_splits_by_weight_source():
    projects = [
        {"weight_kg": 0.5, "weight_source": impact.WEIGHT_USER},
        {"weight_kg": 0.18, "weight_source": impact.WEIGHT_CATEGORY},
    ]
    s = impact.summarize(analyses_count=2, saved_ideas_count=0, projects=projects)
    assert s["garments_reused_estimate"] == 2
    assert s["fabric_kg_diverted_upper_bound"] == pytest.approx(0.68)
    assert s["fabric_kg_from_user_weights"] == pytest.approx(0.5)
    assert s["fabric_kg_from_assumed_weights"] == pytest.approx(0.18)
    assert s["is_estimate"] is True


def test_no_carbon_or_water_numbers_without_verified_factor():
    s = impact.summarize(
        analyses_count=1, saved_ideas_count=0,
        projects=[{"weight_kg": 1.0, "weight_source": impact.WEIGHT_USER}],
    )
    env = s["environmental"]
    assert env["status"] == "not_configured"
    assert env["co2e_kg"] is None and env["water_litres"] is None
    assert not impact.environmental_factors_enabled()


def test_factors_require_a_source_before_being_used(monkeypatch):
    cfg = {
        "default_garment_weight_kg": 0.3, "max_user_weight_kg": 20, "assumptions": ["x"],
        "environmental_factors": {"enabled": True, "co2e_kg_per_kg": 2.0,
                                   "water_litres_per_kg": 100.0, "source": None},
    }
    monkeypatch.setattr(impact, "load_assumptions", lambda: cfg)
    assert not impact.environmental_factors_enabled()  # no source -> still disabled

    cfg["environmental_factors"]["source"] = "Example Study (2020)"
    assert impact.environmental_factors_enabled()
    s = impact.summarize(
        analyses_count=0, saved_ideas_count=0,
        projects=[{"weight_kg": 2.0, "weight_source": impact.WEIGHT_USER}],
    )
    assert s["environmental"]["co2e_kg"] == 4.0
    assert s["environmental"]["water_litres"] == 200
    assert s["environmental"]["source"] == "Example Study (2020)"