"""Unit tests for Phase 4: Damage Detection Module (YOLOv8 & Stub Fallback)."""

import io
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import torch

from backend.app.ml.damage import (
    analyze_damage,
    is_using_stub,
    load_damage_model,
)
from backend.app.schemas import DamageAnalysis


def test_damage_fallback_when_weights_missing():
    """Verify that damage detection falls back to the stub when weights/damage.pt is absent."""
    # Ensure stub mode
    with patch("backend.app.ml.damage.WEIGHTS_PATH") as mock_path:
        mock_path.exists.return_value = False
        loaded = load_damage_model()
        assert loaded is False
        assert is_using_stub() is True

        # Call inference on arbitrary bytes
        res = analyze_damage([b"fake_image_bytes"])
        assert isinstance(res, DamageAnalysis)
        assert res.detected is True
        assert res.area_percent == 6.5
        assert len(res.boxes) == 1
        assert res.boxes[0].label == "tear"


def test_damage_real_inference_with_mock_yolo():
    """Verify that real YOLO prediction correctly parses masks and bounding boxes."""
    # Create mock result object mirroring Ultralytics YOLO Results
    mock_box = MagicMock()
    mock_box.xyxyn = torch.tensor([[0.20, 0.30, 0.40, 0.50]])
    mock_box.cls = torch.tensor([0])
    mock_box.conf = torch.tensor([0.92])

    mock_mask_data = torch.zeros((1, 100, 100))
    mock_mask_data[0, 20:40, 30:50] = 1.0  # 20x20 = 400 pixels out of 10,000 = 4%

    mock_masks = MagicMock()
    mock_masks.data = mock_mask_data

    mock_result = MagicMock()
    mock_result.boxes = [mock_box]
    mock_result.masks = mock_masks
    mock_result.names = {0: "tear"}
    mock_result.orig_shape = (100, 100)

    mock_yolo_model = MagicMock()
    mock_yolo_model.predict.return_value = [mock_result]

    # Create a small valid 100x100 JPEG image in bytes
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buf, format="JPEG")
    valid_img_bytes = buf.getvalue()

    with patch("backend.app.ml.damage._damage_model", mock_yolo_model):
        with patch("backend.app.ml.damage._is_stub_mode", False):
            res = analyze_damage([valid_img_bytes])
            assert isinstance(res, DamageAnalysis)
            assert res.detected is True
            assert res.area_percent == 4.0  # Exactly 400 / 10000 * 100%
            assert len(res.boxes) == 1
            assert res.boxes[0].label == "tear"
            assert res.boxes[0].confidence == 0.92
            assert res.boxes[0].x1 == 0.20
            assert res.boxes[0].y1 == 0.30


def test_analyze_endpoint_with_damage_pipeline(client):
    """Verify that POST /analyze executes the damage detection pipeline cleanly."""
    fake_garment = io.BytesIO(b"fake_garment_jpeg")
    files = [
        ("garment_images", ("front.jpg", fake_garment, "image/jpeg")),
    ]
    response = client.post("/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "damage" in data
    assert isinstance(data["damage"]["detected"], bool)
    assert isinstance(data["damage"]["area_percent"], (int, float))
    assert isinstance(data["damage"]["boxes"], list)
