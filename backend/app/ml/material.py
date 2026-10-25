"""Coarse Fabric Material Classifier (ResNet-18).

Classifies fabric into coarse classes: natural, synthetic, blend, or uncertain.
Loaded ONCE at backend startup (Rule #5).
Enforces configurable confidence threshold gating (default 0.60 per Section 7.3).
Below the threshold, returns 'uncertain' instead of guessing (Non-Negotiable Rule #3).
Falls back gracefully to stub mode if weights/material.pt is absent (Rule #1 & #6).
"""

import io
import logging
from pathlib import Path
from typing import Any, List, Optional
import torch
import torch.nn as nn
from PIL import Image
import torchvision.transforms as transforms
from torchvision.models import resnet18

from backend.app.config import settings
from backend.app.ml.gradcam import generate_gradcam_heatmap
from backend.app.schemas import MaterialAnalysis, MaterialLabel

logger = logging.getLogger("ml.material")

WEIGHTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "weights" / "material.pt"

MATERIAL_CLASSES: List[MaterialLabel] = ["natural", "synthetic", "blend"]

# Standard evaluation transform pipeline
_eval_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

_material_model: Optional[Any] = None
_is_stub_mode: bool = True


def load_material_model() -> bool:
    """Load trained ResNet-18 material weights once at startup."""
    global _material_model, _is_stub_mode

    if not WEIGHTS_PATH.exists():
        logger.warning(
            f"Weights file not found at '{WEIGHTS_PATH}'. "
            "Material classifier will operate in STUB fallback mode."
        )
        _material_model = None
        _is_stub_mode = True
        return False

    try:
        logger.info(f"Loading material classifier weights from '{WEIGHTS_PATH}'...")
        # 1. Build ResNet-18 architecture with 3 output classes
        model = resnet18(weights=None)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, len(MATERIAL_CLASSES))

        # 2. Load state dict
        checkpoint = torch.load(str(WEIGHTS_PATH), map_location="cpu")
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        elif isinstance(checkpoint, dict):
            model.load_state_dict(checkpoint)
        else:
            model = checkpoint

        model.eval()
        _material_model = model
        _is_stub_mode = False
        logger.info("Successfully loaded material classifier model (ResNet-18).")
        return True
    except Exception as e:
        logger.error(
            f"Failed to load material weights from '{WEIGHTS_PATH}': {e}. "
            "Falling back to STUB mode."
        )
        _material_model = None
        _is_stub_mode = True
        return False


def is_using_stub() -> bool:
    return _is_stub_mode


def analyze_material(
    image_bytes_list: List[bytes],
    confidence_threshold: float = settings.CONFIDENCE_THRESHOLD,
) -> MaterialAnalysis:
    """Classify coarse fabric material from uploaded images.

    Enforces confidence threshold gating (Rule #3).
    Averages predictions across all provided photos.
    Falls back gracefully to stub if weights are missing.
    """
    # Use close-up texture image (index 1 if available, else index 0) for material attention
    texture_img_bytes = image_bytes_list[1] if len(image_bytes_list) > 1 else (image_bytes_list[0] if image_bytes_list else b"")

    if _is_stub_mode or _material_model is None:
        # Default realistic stub matching docs/PROJECT.md Section 11
        raw_label: MaterialLabel = "natural"
        confidence: float = 0.82

        heatmap_b64 = generate_gradcam_heatmap(
            model=None,
            target_layer=None,
            image_bytes=texture_img_bytes,
            focus_center=(0.5, 0.5),
        )

        # Gated by configured confidence threshold
        if confidence < confidence_threshold:
            return MaterialAnalysis(label="uncertain", confidence=confidence, heatmap_base64=heatmap_b64)

        return MaterialAnalysis(label=raw_label, confidence=confidence, heatmap_base64=heatmap_b64)

    # Real ResNet-18 PyTorch inference
    all_probs: List[torch.Tensor] = []

    for img_bytes in image_bytes_list:
        try:
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            tensor = _eval_transforms(image).unsqueeze(0)  # shape (1, 3, 224, 224)
            with torch.no_grad():
                logits = _material_model(tensor)
                probs = torch.softmax(logits, dim=1).squeeze(0)  # shape (3,)
                all_probs.append(probs)
        except Exception as e:
            logger.warning(f"Error processing image in material model: {e}")
            continue

    if not all_probs:
        heatmap_b64 = generate_gradcam_heatmap(
            model=None,
            target_layer=None,
            image_bytes=texture_img_bytes,
            focus_center=(0.5, 0.5),
        )
        return MaterialAnalysis(label="uncertain", confidence=0.0, heatmap_base64=heatmap_b64)

    # Average probabilities across all provided photos
    mean_probs = torch.stack(all_probs).mean(dim=0)
    top_idx = int(torch.argmax(mean_probs).item())
    top_prob = float(mean_probs[top_idx].item())
    raw_label = MATERIAL_CLASSES[top_idx]

    # Confidence Gating: if top probability is below threshold, return 'uncertain'
    final_label: MaterialLabel = raw_label if top_prob >= confidence_threshold else "uncertain"

    # Compute Grad-CAM heatmap using layer4[-1] of ResNet-18
    target_layer = getattr(_material_model, "layer4", [None])[-1]
    heatmap_b64 = generate_gradcam_heatmap(
        model=_material_model,
        target_layer=target_layer,
        image_bytes=texture_img_bytes,
        target_category=top_idx,
        focus_center=(0.5, 0.5),
    )

    return MaterialAnalysis(
        label=final_label,
        confidence=round(top_prob, 2),
        heatmap_base64=heatmap_b64,
    )
