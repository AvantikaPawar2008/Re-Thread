"""Tests for POST /recommend endpoint."""

from backend.app.schemas import RecommendResponse


def test_recommend_pathways(client):
    """Test recommendation engine with analyzed garment data in Pune."""
    payload = {
        "analysis": {
            "material": {"label": "natural", "confidence": 0.82},
            "condition": {"label": "gently_used", "confidence": 0.74},
            "damage": {"detected": True, "area_percent": 6.5, "boxes": []},
            "tag": {
                "brand": "H&M",
                "composition": {"cotton": 60.0, "polyester": 40.0},
                "ocr_confidence": 0.88,
                "agrees_with_vision": True,
            },
            "composition_status": "confident",
        },
        "user_latitude": 18.5204,  # Central Pune
        "user_longitude": 73.8567,
        "garment_weight_kg": 0.5,
    }

    response = client.post("/recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    validated = RecommendResponse.model_validate(data)

    # 1. Check pathways count and ranking order
    assert len(validated.ranked_pathways) == 5
    scores = [p.score for p in validated.ranked_pathways]
    assert scores == sorted(scores, reverse=True), "Pathways must be ranked in descending order"

    # 2. Check that top pathway is repair given 6.5% damage on gently_used garment
    top_pathway = validated.ranked_pathways[0]
    assert top_pathway.pathway == "repair"
    assert top_pathway.eligible is True
    assert top_pathway.nearest_partner is not None
    assert top_pathway.nearest_partner.distance_km > 0.0

    # 3. Check climate impact calculation
    assert top_pathway.impact.water_litres_saved > 0.0
    assert top_pathway.impact.co2_kg_saved > 0.0

    # 4. Check plain-language explanation
    assert "Repair" in validated.explanation
    assert "FC Road" in validated.explanation or "Tailor" in validated.explanation or "nearest" in validated.explanation

    # 5. Check SHAP feature attributions
    assert "material" in validated.shap
    assert "condition" in validated.shap
    assert "damage_percent" in validated.shap

    # 6. Check unique QR identifier
    assert validated.qr_id.startswith("rt-")
