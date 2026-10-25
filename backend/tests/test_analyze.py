"""Tests for POST /analyze endpoint."""

import io
from backend.app.schemas import AnalyzeResponse


def test_analyze_with_garment_and_tag(client):
    """Test full analysis with both garment photo and tag photo."""
    fake_garment_1 = io.BytesIO(b"fake_garment_jpeg_content_1")
    fake_garment_2 = io.BytesIO(b"fake_garment_jpeg_content_2")
    fake_tag = io.BytesIO(b"fake_care_label_content")

    files = [
        ("garment_images", ("garment_front.jpg", fake_garment_1, "image/jpeg")),
        ("garment_images", ("garment_texture.jpg", fake_garment_2, "image/jpeg")),
        ("tag_image", ("care_tag.jpg", fake_tag, "image/jpeg")),
    ]

    response = client.post("/analyze", files=files)
    assert response.status_code == 200

    data = response.json()
    # Validate against strict Pydantic schema
    validated = AnalyzeResponse.model_validate(data)

    # Material checks
    assert validated.material.label in ("natural", "synthetic", "blend", "uncertain")
    assert 0.0 <= validated.material.confidence <= 1.0

    # Condition checks
    assert validated.condition.label in ("new", "gently_used", "worn", "heavily_worn")
    assert 0.0 <= validated.condition.confidence <= 1.0

    # Damage checks
    assert isinstance(validated.damage.detected, bool)
    assert 0.0 <= validated.damage.area_percent <= 100.0

    # Tag checks
    assert validated.tag.brand == "H&M"
    assert "cotton" in validated.tag.composition
    assert validated.composition_status in ("confident", "uncertain")


def test_analyze_without_tag_degrades_gracefully(client):
    """Test graceful degradation when care tag is absent (Rule #6)."""
    fake_garment = io.BytesIO(b"fake_garment_bytes")
    files = [
        ("garment_images", ("garment.jpg", fake_garment, "image/jpeg")),
    ]

    response = client.post("/analyze", files=files)
    assert response.status_code == 200

    data = response.json()
    validated = AnalyzeResponse.model_validate(data)

    # Tag should be cleanly absent/empty without crashing
    assert validated.tag.brand is None
    assert validated.tag.composition == {}
    assert validated.tag.ocr_confidence == 0.0
    assert validated.composition_status in ("confident", "uncertain")


def test_analyze_missing_images_fails(client):
    """Test that missing required garment images returns 422."""
    response = client.post("/analyze", files=[])
    assert response.status_code == 422
