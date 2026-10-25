"""Garment Damage Detection & Defect Area Segmentation.

Uses an Ultralytics YOLOv8 segmentation model (`weights/damage.pt`).
Loaded ONCE at startup (Rule #5).
If the weights file is absent, gracefully falls back to the stub (Rule #1 & Rule #6).
"""

import io
import logging
from pathlib import Path
from typing import Any, List, Optional
import numpy as np
from PIL import Image

from backend.app.schemas import DamageAnalysis, DamageBox

logger = logging.getLogger("ml.damage")

# Expected weights location
WEIGHTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "weights" / "damage.pt"

# Module-level model holder loaded once at startup
_damage_model: Optional[Any] = None
_is_stub_mode: bool = True


def load_damage_model() -> bool:
    """Load trained YOLOv8 weights once at backend startup.

    Returns True if weights loaded successfully, False if falling back to stub.
    """
    global _damage_model, _is_stub_mode

    if not WEIGHTS_PATH.exists():
        logger.warning(
            f"Weights file not found at '{WEIGHTS_PATH}'. "
            "Garment damage detection will operate in STUB fallback mode."
        )
        _damage_model = None
        _is_stub_mode = True
        return False

    try:
        from ultralytics import YOLO

        logger.info(f"Loading damage detection weights from '{WEIGHTS_PATH}'...")
        _damage_model = YOLO(str(WEIGHTS_PATH))
        _is_stub_mode = False
        logger.info("Successfully loaded damage detection model (YOLOv8).")
        return True
    except Exception as e:
        logger.error(
            f"Failed to load weights from '{WEIGHTS_PATH}': {e}. "
            "Falling back to STUB mode."
        )
        _damage_model = None
        _is_stub_mode = True
        return False


def is_using_stub() -> bool:
    """Return True if operating in fallback stub mode."""
    return _is_stub_mode


def analyze_damage(image_bytes_list: List[bytes]) -> DamageAnalysis:
    """Analyze garment images for visible damage (tears, holes, stains).

    If model weights are loaded, runs inference and computes mask area %.
    If in stub mode, returns realistic simulated output in the contract shape.
    """
    if _is_stub_mode or _damage_model is None:
        # Graceful STUB fallback output matching docs/PROJECT.md Section 11
        sample_box = DamageBox(
            x1=0.35,
            y1=0.45,
            x2=0.48,
            y2=0.58,
            label="tear",
            confidence=0.89,
        )
        return DamageAnalysis(
            detected=True,
            area_percent=6.5,
            boxes=[sample_box],
        )

    # Real YOLOv8 Inference
    detected_boxes: List[DamageBox] = []
    max_area_pct: float = 0.0

    for img_bytes in image_bytes_list:
        try:
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            # Run YOLO prediction
            results = _damage_model.predict(source=image, conf=0.25, verbose=False)

            for r in results:
                # 1. Extract bounding boxes
                if r.boxes is not None and len(r.boxes) > 0:
                    for i, box in enumerate(r.boxes):
                        # Normalized xyxyn coordinates (0.0 to 1.0)
                        xyxy_norm = box.xyxyn[0].cpu().numpy()
                        cls_idx = int(box.cls[0].cpu().item())
                        cls_name = r.names.get(cls_idx, "defect")
                        conf = float(box.conf[0].cpu().item())

                        detected_boxes.append(
                            DamageBox(
                                x1=round(float(xyxy_norm[0]), 3),
                                y1=round(float(xyxy_norm[1]), 3),
                                x2=round(float(xyxy_norm[2]), 3),
                                y2=round(float(xyxy_norm[3]), 3),
                                label=cls_name,
                                confidence=round(conf, 2),
                            )
                        )

                # 2. Extract damage area percentage from segmentation masks
                if r.masks is not None and len(r.masks) > 0:
                    # Union mask across all detected defect instances
                    masks_arr = r.masks.data.cpu().numpy()  # shape (N, H, W)
                    combined_mask = np.any(masks_arr > 0.5, axis=0)
                    mask_pixel_count = np.sum(combined_mask)
                    total_pixel_count = combined_mask.shape[0] * combined_mask.shape[1]
                    area_pct = (mask_pixel_count / max(1, total_pixel_count)) * 100.0
                    max_area_pct = max(max_area_pct, area_pct)
                elif detected_boxes:
                    # Fallback to normalized box area if masks are unavailable
                    box_area = sum(
                        (b.x2 - b.x1) * (b.y2 - b.y1) * 100.0 for b in detected_boxes
                    )
                    max_area_pct = max(max_area_pct, min(100.0, box_area))

        except Exception as e:
            logger.warning(f"Error analyzing image for damage: {e}")
            continue

    has_damage = len(detected_boxes) > 0 or max_area_pct > 0.0

    return DamageAnalysis(
        detected=has_damage,
        area_percent=round(max_area_pct, 1),
        boxes=detected_boxes,
    )
