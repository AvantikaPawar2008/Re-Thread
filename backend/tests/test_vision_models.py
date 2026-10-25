"""Unit tests for Phase 5: Condition & Material ResNet-18 Classifiers."""

import io
from unittest.mock import MagicMock, patch
from PIL import Image
import pytest
import torch

from backend.app.ml.condition import (
    analyze_condition,
    is_using_stub as condition_is_stub,
    load_condition_model,
)
from backend.app.ml.material import (
    analyze_material,
    is_using_stub as material_is_stub,
    load_material_model,
)
from backend.app.schemas import ConditionAnalysis, MaterialAnalysis


def create_dummy_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), color="green").save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Condition Model Tests
# ---------------------------------------------------------------------------
def test_condition_fallback_when_weights_missing():
    """Verify condition classifier falls back to stub when weights/condition.pt is absent."""
    with patch("backend.app.ml.condition.WEIGHTS_PATH") as mock_path:
        mock_path.exists.return_value = False
        loaded = load_condition_model()
        assert loaded is False
        assert condition_is_stub() is True

        res = analyze_condition([b"arbitrary_bytes"])
        assert isinstance(res, ConditionAnalysis)
        assert res.label in ("new", "gently_used", "worn", "heavily_worn")
        assert 0.0 <= res.confidence <= 1.0


def test_condition_inference_with_mock_model():
    """Verify PyTorch softmax classification and class index mapping for condition."""
    # Mock ResNet-18 returning high logits for 'worn' (index 2: new, gently_used, worn, heavily_worn)
    mock_model = MagicMock()
    mock_model.return_value = torch.tensor([[1.0, 2.0, 8.0, 1.0]])  # High probability for 'worn'

    img_bytes = create_dummy_jpeg_bytes()

    with patch("backend.app.ml.condition._condition_model", mock_model):
        with patch("backend.app.ml.condition._is_stub_mode", False):
            res = analyze_condition([img_bytes])
            assert isinstance(res, ConditionAnalysis)
            assert res.label == "worn"
            assert res.confidence > 0.85


# ---------------------------------------------------------------------------
# Material Model Tests
# ---------------------------------------------------------------------------
def test_material_fallback_when_weights_missing():
    """Verify material classifier falls back to stub when weights/material.pt is absent."""
    with patch("backend.app.ml.material.WEIGHTS_PATH") as mock_path:
        mock_path.exists.return_value = False
        loaded = load_material_model()
        assert loaded is False
        assert material_is_stub() is True

        res = analyze_material([b"arbitrary_bytes"])
        assert isinstance(res, MaterialAnalysis)
        assert res.label in ("natural", "synthetic", "blend", "uncertain")
        assert 0.0 <= res.confidence <= 1.0


def test_material_confidence_threshold_gating():
    """Verify that if model confidence falls below threshold (default 0.60), label becomes 'uncertain'."""
    # Logits produce an ambiguous split: ~0.40 natural, ~0.35 synthetic, ~0.25 blend
    mock_model = MagicMock()
    mock_model.return_value = torch.tensor([[2.0, 1.8, 1.5]])  # Max prob ~0.40, below 0.60 threshold

    img_bytes = create_dummy_jpeg_bytes()

    with patch("backend.app.ml.material._material_model", mock_model):
        with patch("backend.app.ml.material._is_stub_mode", False):
            res = analyze_material([img_bytes], confidence_threshold=0.60)
            assert isinstance(res, MaterialAnalysis)
            assert res.label == "uncertain"
            assert res.confidence < 0.60

            # If threshold is relaxed to 0.30, raw label is exposed
            res_relaxed = analyze_material([img_bytes], confidence_threshold=0.30)
            assert res_relaxed.label == "natural"


def test_material_inference_with_confident_mock():
    """Verify that a confident prediction above threshold returns the coarse label."""
    mock_model = MagicMock()
    mock_model.return_value = torch.tensor([[10.0, 1.0, 1.0]])  # ~99% natural

    img_bytes = create_dummy_jpeg_bytes()

    with patch("backend.app.ml.material._material_model", mock_model):
        with patch("backend.app.ml.material._is_stub_mode", False):
            res = analyze_material([img_bytes], confidence_threshold=0.60)
            assert isinstance(res, MaterialAnalysis)
            assert res.label == "natural"
            assert res.confidence > 0.95


def test_analyze_endpoint_integrates_vision_models(client):
    """Verify that POST /analyze executes all vision models together cleanly."""
    fake_front = io.BytesIO(create_dummy_jpeg_bytes())
    fake_texture = io.BytesIO(create_dummy_jpeg_bytes())

    files = [
        ("garment_images", ("front.jpg", fake_front, "image/jpeg")),
        ("garment_images", ("texture.jpg", fake_texture, "image/jpeg")),
    ]
    response = client.post("/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["material"]["label"] in ("natural", "synthetic", "blend", "uncertain")
    assert data["condition"]["label"] in ("new", "gently_used", "worn", "heavily_worn")
    assert "damage" in data
    assert "tag" in data
