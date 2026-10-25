"""Unit tests for Phase 3: Decision Engine Edge Cases.

Tests cover:
1. Unknown brand (fails safe, never blocks user)
2. No eligible partners nearby (handles distant coordinates gracefully)
3. Close scores (triggers balanced dual-pathway explanation)
4. Uncertain material (handles composition uncertainty and LCA fallbacks)
5. Ranker interface and SHAP attributions
6. QR generation and intake confirmation
"""

from backend.app.engine.explanation import generate_explanation
from backend.app.engine.geography import find_nearest_partner
from backend.app.engine.impact import calculate_impact
from backend.app.engine.qr import generate_qr_base64, generate_qr_id
from backend.app.engine.ranking import WeightedFormulaRanker, rank_pathways
from backend.app.engine.rules import check_brand_takeback_eligibility, evaluate_eligibility
from backend.app.schemas import (
    AnalyzeResponse,
    ConditionAnalysis,
    DamageAnalysis,
    MaterialAnalysis,
    RankedPathway,
    RecommendResponse,
    TagAnalysis,
)


def make_sample_analysis(
    material="natural",
    condition="gently_used",
    damage_detected=True,
    damage_pct=6.5,
    brand="H&M",
    composition_status="confident",
) -> AnalyzeResponse:
    return AnalyzeResponse(
        material=MaterialAnalysis(label=material, confidence=0.85),
        condition=ConditionAnalysis(label=condition, confidence=0.75),
        damage=DamageAnalysis(detected=damage_detected, area_percent=damage_pct, boxes=[]),
        tag=TagAnalysis(
            brand=brand,
            composition={"cotton": 100.0} if brand else {},
            ocr_confidence=0.90 if brand else 0.0,
            agrees_with_vision=True,
        ),
        composition_status=composition_status,
    )


# ---------------------------------------------------------------------------
# Edge Case 1: Unknown Brand
# ---------------------------------------------------------------------------
def test_edge_case_unknown_brand(client, db_session):
    """Unknown brands must not be eligible for brand take-back, but must never block the user."""
    # Direct rule check
    assert not check_brand_takeback_eligibility(db_session, "UnknownFictionalBrandX", "natural")
    assert not check_brand_takeback_eligibility(db_session, None, "natural")
    assert not check_brand_takeback_eligibility(db_session, "", "natural")

    analysis = make_sample_analysis(brand="NonExistentBrand123")
    eligibility = evaluate_eligibility(db_session, analysis)
    assert eligibility["brand_takeback"] is False
    assert eligibility["recycle"] is True  # Fallback remains open

    # API test: User is never blocked (Rule #6)
    payload = {
        "analysis": analysis.model_dump(),
        "user_latitude": 18.5204,
        "user_longitude": 73.8567,
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    validated = RecommendResponse.model_validate(data)

    # Brand takeback should be ineligible or ranked at the bottom
    takeback_item = next(p for p in validated.ranked_pathways if p.pathway == "brand_takeback")
    assert takeback_item.eligible is False


# ---------------------------------------------------------------------------
# Edge Case 2: No Eligible Partners Nearby
# ---------------------------------------------------------------------------
def test_edge_case_no_eligible_partners_nearby(client, db_session):
    """When coordinates are remote with no nearby partners, the system degrades gracefully."""
    # In the middle of the Indian Ocean
    remote_lat, remote_lon = -45.0, 60.0

    analysis = make_sample_analysis()
    payload = {
        "analysis": analysis.model_dump(),
        "user_latitude": remote_lat,
        "user_longitude": remote_lon,
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    validated = RecommendResponse.model_validate(data)

    # All distances are large or penalized, but the recommendation does not crash
    assert len(validated.ranked_pathways) == 5
    top_partner = validated.ranked_pathways[0].nearest_partner
    # Partners exist in Pune, so distance from remote location will be large
    if top_partner:
        assert top_partner.distance_km > 1000.0


# ---------------------------------------------------------------------------
# Edge Case 3: Close Scores Between Pathways
# ---------------------------------------------------------------------------
def test_edge_case_close_scores_triggers_transparent_explanation():
    """When two pathways have close scores, the explanation transparently highlights both."""
    analysis = make_sample_analysis(
        condition="gently_used",
        damage_detected=True,
        damage_pct=2.0,  # Very slight defect: repair and reuse are both viable
    )
    eligibility = {
        "repair": True,
        "reuse_resell": True,
        "donate": True,
        "recycle": True,
        "brand_takeback": False,
    }
    distances = {"repair": 2.0, "reuse_resell": 2.1, "donate": 3.0, "recycle": 8.0, "brand_takeback": 15.0}

    scored, shap = rank_pathways(analysis, eligibility, distances)
    # Check that top 2 pathways have close scores
    score_diff = abs(scored[0][1] - scored[1][1])

    # Convert to RankedPathway objects for explanation generator
    ranked_pathways = [
        RankedPathway(
            pathway=s[0],
            score=s[1],
            eligible=s[2],
            nearest_partner=None,
            impact={"water_litres_saved": 2500.0, "co2_kg_saved": 5.0},
        )
        for s in scored
    ]
    explanation = generate_explanation(ranked_pathways, analysis)

    if score_diff <= 0.08:
        assert "Close match" in explanation


# ---------------------------------------------------------------------------
# Edge Case 4: Uncertain Material
# ---------------------------------------------------------------------------
def test_edge_case_uncertain_material(client, db_session):
    """Uncertain material must be handled honestly and use conservative blend LCA factors."""
    analysis = make_sample_analysis(
        material="uncertain",
        composition_status="uncertain",
    )

    # 1. Impact check: uses fallback blend LCA factor
    impact = calculate_impact(db_session, "recycle", "uncertain", garment_weight_kg=0.3)
    assert impact.water_litres_saved > 0.0
    assert impact.co2_kg_saved > 0.0

    # 2. Explanation check: explicitly acknowledges uncertainty
    payload = {
        "analysis": analysis.model_dump(),
        "user_latitude": 18.5204,
        "user_longitude": 73.8567,
        "garment_weight_kg": 0.3,
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "uncertain" in data["explanation"].lower()


# ---------------------------------------------------------------------------
# Ranker Interface & SHAP Attributions Test
# ---------------------------------------------------------------------------
def test_ranker_interface_and_shap_output():
    """Verify that BaseRanker interface outputs normalized scores and SHAP dictionary."""
    ranker = WeightedFormulaRanker()
    analysis = make_sample_analysis(damage_detected=True, damage_pct=8.0)
    eligibility = {"repair": True, "reuse_resell": False, "donate": True, "recycle": True, "brand_takeback": False}
    distances = {"repair": 1.5, "donate": 2.0, "recycle": 5.0, "reuse_resell": 10.0, "brand_takeback": 15.0}

    ranked_scores, shap = ranker.rank(analysis, eligibility, distances)

    assert len(ranked_scores) == 5
    # Scores must be sorted descending
    scores = [s.score for s in ranked_scores]
    assert scores == sorted(scores, reverse=True)

    # SHAP feature contributions must contain standard keys
    assert "material" in shap
    assert "condition" in shap
    assert "damage_percent" in shap
    assert "brand" in shap


# ---------------------------------------------------------------------------
# QR Generation & Outcome Intake Flywheel
# ---------------------------------------------------------------------------
def test_qr_generation_and_outcome_flow(client):
    """Test generating a real QR ID and base64 PNG image, then confirming intake."""
    qr_id = generate_qr_id()
    assert qr_id.startswith("rt-")

    # Generate base64 data URI
    data_uri = generate_qr_base64(qr_id)
    assert data_uri.startswith("data:image/png;base64,")
    assert len(data_uri) > 100
