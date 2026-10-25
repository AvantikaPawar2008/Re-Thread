"""Care Tag Image Preprocessing & Cleaning (OpenCV).

Performs deskew, CLAHE (Contrast Limited Adaptive Histogram Equalization),
and adaptive binarization to optimize small, faded, or rotated care labels for OCR.
"""

import logging
import cv2
import numpy as np

logger = logging.getLogger("ml.tag.clean")


def deskew_image(gray: np.ndarray) -> np.ndarray:
    """Detect text skew angle and rotate image to upright orientation."""
    try:
        # Invert: text becomes white, background black
        thresh = cv2.bitwise_not(gray)
        # Find all coordinates of foreground pixels
        coords = np.column_stack(np.where(thresh > 50))
        if coords.shape[0] < 50:
            return gray

        # Compute minimum area bounding box
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]

        # Adjust angle orientation
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # If angle is negligible or extreme (error), skip rotation
        if abs(angle) < 0.5 or abs(angle) > 45.0:
            return gray

        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return rotated
    except Exception as e:
        logger.debug(f"Deskew skipped: {e}")
        return gray


def apply_clahe(gray: np.ndarray) -> np.ndarray:
    """Enhance local contrast for faded ink on satin or fabric care tags."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def binarize_image(gray: np.ndarray) -> np.ndarray:
    """Apply slight Gaussian blur followed by Otsu thresholding."""
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def clean_tag_image(crop_bytes: bytes) -> bytes:
    """Full OpenCV cleaning pipeline for care tag crops.

    1. Decode image bytes
    2. Convert to Grayscale
    3. Deskew orientation
    4. Enhance contrast via CLAHE
    5. Adaptive binarization
    6. Return preprocessed image bytes
    """
    if not crop_bytes:
        return crop_bytes

    try:
        np_arr = np.frombuffer(crop_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return crop_bytes

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Deskew
        deskewed = deskew_image(gray)

        # 3. CLAHE contrast enhancement
        enhanced = apply_clahe(deskewed)

        # 4. Binarization
        binarized = binarize_image(enhanced)

        # Encode back to PNG bytes
        success, encoded = cv2.imencode(".png", binarized)
        if success:
            return encoded.tobytes()

        return crop_bytes
    except Exception as e:
        logger.warning(f"Error cleaning tag image: {e}")
        return crop_bytes
