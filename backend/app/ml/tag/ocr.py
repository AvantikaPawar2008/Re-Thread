"""Care Tag Optical Character Recognition (PaddleOCR).

Reads text lines and confidence scores from preprocessed care labels.
Loaded ONCE at backend startup (Rule #5).
Falls back gracefully if PaddleOCR is not installed or fails (Rule #1 & #6).
"""

import io
import logging
from typing import Any, List, Optional, Tuple
import numpy as np
from PIL import Image

logger = logging.getLogger("ml.tag.ocr")

_paddle_ocr: Optional[Any] = None
_is_stub_mode: bool = True


def load_ocr_engine() -> bool:
    """Initialize PaddleOCR engine once at startup."""
    global _paddle_ocr, _is_stub_mode

    try:
        from paddleocr import PaddleOCR

        logger.info("Initializing PaddleOCR engine (lang='en')...")
        _paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        _is_stub_mode = False
        logger.info("PaddleOCR engine loaded successfully.")
        return True
    except Exception as e:
        logger.warning(
            f"PaddleOCR is not available ({e}). "
            "Tag text extraction will operate in fallback mode."
        )
        _paddle_ocr = None
        _is_stub_mode = True
        return False


def is_using_stub() -> bool:
    return _is_stub_mode


def extract_tag_text(cleaned_crop_bytes: bytes) -> List[Tuple[str, float]]:
    """Extract (text_line, confidence) pairs using PaddleOCR.

    Returns list of tuples e.g. [("H&M", 0.95), ("60% COTTON", 0.91), ...]
    Falls back gracefully if OCR engine is unavailable.
    """
    if not cleaned_crop_bytes:
        return []

    if _is_stub_mode or _paddle_ocr is None:
        # Standard simulated OCR text for development testing
        return [
            ("H&M", 0.95),
            ("60% COTTON", 0.92),
            ("40% POLYESTER", 0.88),
            ("MADE IN INDIA", 0.89),
            ("WASH AT 40C", 0.90),
        ]

    try:
        # Decode image to RGB numpy array for PaddleOCR
        image = Image.open(io.BytesIO(cleaned_crop_bytes)).convert("RGB")
        img_np = np.array(image)

        # Run OCR
        result = _paddle_ocr.ocr(img_np, cls=True)
        extracted: List[Tuple[str, float]] = []

        if result and len(result) > 0 and result[0] is not None:
            for line in result[0]:
                text_info = line[1]
                text = str(text_info[0]).strip().upper()
                confidence = float(text_info[1])
                if text:
                    extracted.append((text, round(confidence, 2)))

        return extracted
    except Exception as e:
        logger.warning(f"Error executing PaddleOCR: {e}")
        return []
