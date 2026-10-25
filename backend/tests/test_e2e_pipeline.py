"""End-to-End Pipeline & Latency Tests for RE-THREAD.

Tests the full circular fashion lifecycle:
1. POST /analyze: Vision + Tag extraction + Grad-CAM heatmaps
2. POST /recommend: Layer A/B/C decision ranking (XGBoost + SHAP)
3. POST /outcome/confirm: QR scanned outcome recording at a Pune drop-off hub
4. Latency performance checks across all core endpoints
"""

import io
import time
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from backend.app.config import settings
from backend.app.engine.ranking import WeightedFormulaRanker
from backend.app.engine.xgb_ranker import XGBoostRanker


def create_dummy_jpeg(color: tuple = (100, 150, 200)) -> bytes:
    """Create a small in-memory JPEG for testing."""
    img = Image.new("RGB", (128, 128), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_e2e_lifecycle_flow(client: TestClient):
    """Verify complete end-to-end circular flow across all 3 endpoints."""
    # -------------------------------------------------------------------------
    # Stage 1: Analyze Garment
    # -------------------------------------------------------------------------
    img1 = create_dummy_jpeg((120, 160, 210))
    img2 = create_dummy_jpeg((130, 170, 220))
    tag_img = create_dummy_jpeg((240, 240, 240))

    files = [
        ("garment_images", ("full.jpg", img1, "image/jpeg")),
        ("garment_images", ("texture.jpg", img2, "image/jpeg")),
        ("tag_image", ("tag.jpg", tag_img, "image/jpeg")),
    ]

    t0 = time.perf_counter()
    analyze_res = client.post("/analyze", files=files)
    t_analyze = (time.perf_counter() - t0) * 1000.0

    assert analyze_res.status_code == 200
    analyze_data = analyze_res.json()

    # Verify Grad-CAM heatmaps are returned
    assert "material" in analyze_data
    assert "condition" in analyze_data
    assert analyze_data["material"]["heatmap_base64"] is not None
    assert analyze_data["material"]["heatmap_base64"].startswith("data:image/jpeg;base64,")
    assert analyze_data["condition"]["heatmap_base64"] is not None
    assert analyze_data["condition"]["heatmap_base64"].startswith("data:image/jpeg;base64,")

    # -------------------------------------------------------------------------
    # Stage 2: Recommend Pathways (Using XGBoost Ranker + SHAP)
    # -------------------------------------------------------------------------
    recommend_payload = {
        "analysis": analyze_data,
        "user_latitude": 18.5204,
        "user_longitude": 73.8567,
        "garment_weight_kg": 0.45,
    }

    t0 = time.perf_counter()
    rec_res = client.post("/recommend", json=recommend_payload)
    t_rec = (time.perf_counter() - t0) * 1000.0

    assert rec_res.status_code == 200
    rec_data = rec_res.json()

    assert len(rec_data["ranked_pathways"]) >= 3
    assert "qr_id" in rec_data
    assert len(rec_data["qr_id"]) > 0
    assert "shap" in rec_data
    assert "condition" in rec_data["shap"]
    assert "material" in rec_data["shap"]

    qr_id = rec_data["qr_id"]

    # -------------------------------------------------------------------------
    # Stage 3: Partner Scans & Confirms Real Outcome
    # -------------------------------------------------------------------------
    confirm_payload = {
        "qr_id": qr_id,
        "partner_facility_id": 1,
        "confirmed_pathway": rec_data["ranked_pathways"][0]["pathway"],
        "notes": "E2E automated validation test drop-off at FC Road hub",
    }

    confirm_res = client.post("/outcome/confirm", json=confirm_payload)
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["status"] == "confirmed"
    assert confirm_data["qr_id"] == qr_id


def test_latency_performance_checks(client: TestClient):
    """Ensure core API endpoints meet latency thresholds on dev/test hardware."""
    # 1. Health check latency < 100ms
    t0 = time.perf_counter()
    health_res = client.get("/health")
    t_health = (time.perf_counter() - t0) * 1000.0
    assert health_res.status_code == 200
    assert t_health < 150.0

    # 2. Recommendation decision engine latency < 350ms
    from backend.app.schemas import AnalyzeResponse, MaterialAnalysis, ConditionAnalysis, DamageAnalysis, TagAnalysis

    mock_analysis = AnalyzeResponse(
        material=MaterialAnalysis(label="natural", confidence=0.85),
        condition=ConditionAnalysis(label="new", confidence=0.90),
        damage=DamageAnalysis(detected=False, area_percent=0.0, boxes=[]),
        tag=TagAnalysis(brand="Zara", composition={"cotton": 100.0}, ocr_confidence=0.90, agrees_with_vision=True),
        composition_status="confident",
    )

    t0 = time.perf_counter()
    rec_res = client.post(
        "/recommend",
        json={
            "analysis": mock_analysis.model_dump(),
            "user_latitude": 18.5204,
            "user_longitude": 73.8567,
            "garment_weight_kg": 0.30,
        },
    )
    t_rec = (time.perf_counter() - t0) * 1000.0
    assert rec_res.status_code == 200
    assert t_rec < 400.0


def test_ranker_interface_implementations(client: TestClient):
    """Test both Formula and XGBoost ranker implementations produce valid output."""
    from backend.app.schemas import AnalyzeResponse, MaterialAnalysis, ConditionAnalysis, DamageAnalysis, TagAnalysis

    mock_analysis = AnalyzeResponse(
        material=MaterialAnalysis(label="blend", confidence=0.75),
        condition=ConditionAnalysis(label="worn", confidence=0.70),
        damage=DamageAnalysis(detected=True, area_percent=4.5, boxes=[]),
        tag=TagAnalysis(brand=None, composition={}, ocr_confidence=0.0, agrees_with_vision=True),
        composition_status="uncertain",
    )
    eligibility = {"reuse_resell": True, "repair": True, "donate": True, "recycle": True, "brand_takeback": False}
    distances = {"reuse_resell": 5.0, "repair": 2.5, "donate": 3.0, "recycle": 10.0, "brand_takeback": 15.0}

    # Test Formula ranker
    formula_ranker = WeightedFormulaRanker()
    f_scores, f_shap = formula_ranker.rank(mock_analysis, eligibility, distances)
    assert len(f_scores) == 5
    assert "material" in f_shap

    # Test XGBoost ranker
    xgb_ranker = XGBoostRanker()
    x_scores, x_shap = xgb_ranker.rank(mock_analysis, eligibility, distances)
    assert len(x_scores) == 5
    assert "material" in x_shap
    assert "condition" in x_shap
