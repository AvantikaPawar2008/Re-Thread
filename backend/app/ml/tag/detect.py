"""Care Tag Detection Module (Fine-Tuned Ultralytics YOLOv8).

Localizes the care label region in a garment photograph.
Loaded ONCE at backend startup (Rule #5).
Falls back gracefully if weights/tag.pt is absent (Rule #1 & #6).
"""

import io
import logging
from pathlib import Path
from typing import Any, Optional, Tuple
from PIL import Image

logger = logging.getLogger("ml.tag.detect")

WEIGHTS_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "weights" / "tag.pt"

_tag_model: Optional[Any] = None
_is_stub_mode: bool = True


def load_tag_detector() -> bool:
    """Load fine-tuned YOLOv8 care tag detector weights once at startup."""
    global _tag_model, _is_stub_mode

    if not WEIGHTS_PATH.exists():
        logger.warning(
            f"Weights file not found at '{WEIGHTS_PATH}'. "
            "Tag detector will operate in STUB fallback mode."
        )
        _tag_model = None
        _is_stub_mode = True
        return False

    try:
        from ultralytics import YOLO

        logger.info(f"Loading tag detector weights from '{WEIGHTS_PATH}'...")
        _tag_model = YOLO(str(WEIGHTS_PATH))
        _is_stub_mode = False
        logger.info("Successfully loaded tag detector model (YOLOv8).")
        return True
    except Exception as e:
        logger.error(f"Failed to load tag weights from '{WEIGHTS_PATH}': {e}. Falling back to STUB mode.")
        _tag_model = None
        _is_stub_mode = True
        return False


def is_using_stub() -> bool:
    return _is_stub_mode


def detect_tag(image_bytes: bytes) -> Optional[Tuple[int, int, int, int]]:
    """Detect care tag bounding box (x1, y1, x2, y2) in image pixels.

    Returns (x1, y1, x2, y2) or None if no tag is found in the photo.
    """
    if not image_bytes:
        return None

    if _is_stub_mode or _tag_model is None:
        # Default simulated crop for development (centered region)
        try:
            image = Image.open(io.BytesIO(image_bytes))
            w, h = image.size
            return (int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8))
        except Exception:
            return (100, 150, 400, 600)

    # Real YOLOv8 inference
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = image.size
        results = _tag_model.predict(source=image, conf=0.25, verbose=False)

        best_box = None
        highest_conf = 0.0

        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                for box in r.boxes:
                    conf = float(box.conf[0].cpu().item())
                    if conf > highest_conf:
                        highest_conf = conf
                        xyxy = box.xyxy[0].cpu().numpy()
                        best_box = (
                            max(0, int(xyxy[0])),
                            max(0, int(xyxy[1])),
                            min(w, int(xyxy[2])),
                            min(h, int(xyxy[3])),
                        )

        return best_box
    except Exception as e:
        logger.warning(f"Error detecting tag with YOLO: {e}")
        return None
