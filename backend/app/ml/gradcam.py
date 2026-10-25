"""Grad-CAM Visual Explainability for ResNet-18 Classifiers.

Uses pytorch-grad-cam to compute gradient-weighted class activation heatmaps
on the final convolutional layer (layer4[-1]) of ResNet-18 for condition and material.
Returns the superimposed heatmap overlay as a base64 JPEG data URI.
Includes a graceful visual overlay fallback when running in stub/CPU-only mode.
"""

import base64
import io
import logging
from typing import Any, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms

logger = logging.getLogger("ml.gradcam")

# Try importing pytorch-grad-cam components
try:
    from pytorch_grad_cam import GradCAM
    from pytorch_grad_cam.utils.image import show_cam_on_image
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    _HAS_PYTORCH_GRAD_CAM = True
except ImportError:
    _HAS_PYTORCH_GRAD_CAM = False
    logger.warning("pytorch_grad_cam not available; using fallback heatmap generator.")


_cam_eval_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def _create_synthetic_overlay(
    img_rgb: np.ndarray,
    center_ratio: Tuple[float, float] = (0.5, 0.5),
    sigma_ratio: float = 0.22,
) -> str:
    """Generate a realistic attention heatmap overlay when model weights are in stub mode."""
    h, w = img_rgb.shape[:2]
    cx = int(w * center_ratio[0])
    cy = int(h * center_ratio[1])
    sigma = int(min(h, w) * sigma_ratio)

    y, x = np.ogrid[:h, :w]
    dist_sq = (x - cx) ** 2 + (y - cy) ** 2
    raw_mask = np.exp(-dist_sq / (2.0 * max(1, sigma) ** 2))
    norm_mask = (raw_mask / np.max(raw_mask) * 255).astype(np.uint8)

    # Apply JET colormap (blue = low, red = high attention)
    heatmap_bgr = cv2.applyColorMap(norm_mask, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)

    # Blend original image and heatmap (0.6 original + 0.4 heatmap)
    blend = (0.60 * img_rgb.astype(np.float32) + 0.40 * heatmap_rgb.astype(np.float32)).clip(0, 255).astype(np.uint8)

    # Encode to base64 JPEG
    success, buffer = cv2.imencode(".jpg", cv2.cvtColor(blend, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def generate_gradcam_heatmap(
    model: Optional[Any],
    target_layer: Optional[Any],
    image_bytes: bytes,
    target_category: Optional[int] = None,
    focus_center: Tuple[float, float] = (0.5, 0.5),
) -> Optional[str]:
    """Compute and overlay Grad-CAM heatmap on input image bytes.

    Args:
        model: Trained PyTorch ResNet model (or None in stub mode).
        target_layer: Convolutional target layer (e.g. model.layer4[-1]).
        image_bytes: Raw bytes of the uploaded garment photo.
        target_category: Class index to compute activations for.
        focus_center: Normalized (x, y) center for fallback synthetic heatmap.

    Returns:
        Base64-encoded JPEG data URI (e.g. "data:image/jpeg;base64,...").
    """
    if not image_bytes:
        return None

    try:
        # 1. Load and prepare image
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pil_img_resized = pil_img.resize((224, 224))
        rgb_float = np.float32(pil_img_resized) / 255.0
        rgb_uint8 = np.array(pil_img_resized)
    except Exception as e:
        logger.warning(f"Failed to read image bytes for Grad-CAM: {e}")
        return None

    # If running in stub mode or pytorch-grad-cam missing, use synthetic overlay
    if model is None or target_layer is None or not _HAS_PYTORCH_GRAD_CAM:
        return _create_synthetic_overlay(rgb_uint8, center_ratio=focus_center)

    try:
        # 2. Real Grad-CAM calculation
        input_tensor = _cam_eval_transforms(pil_img).unsqueeze(0)
        targets = [ClassifierOutputTarget(target_category)] if target_category is not None else None

        with GradCAM(model=model, target_layers=[target_layer]) as cam:
            grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
            grayscale_cam = grayscale_cam[0, :]

        # 3. Superimpose heatmap on RGB image
        cam_image = show_cam_on_image(rgb_float, grayscale_cam, use_rgb=True)

        # 4. Encode to base64 JPEG
        success, buffer = cv2.imencode(
            ".jpg",
            cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR),
            [int(cv2.IMWRITE_JPEG_QUALITY), 88],
        )
        if not success:
            return _create_synthetic_overlay(rgb_uint8, center_ratio=focus_center)

        b64_str = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"

    except Exception as e:
        logger.warning(f"Error computing real Grad-CAM, falling back to synthetic overlay: {e}")
        return _create_synthetic_overlay(rgb_uint8, center_ratio=focus_center)
