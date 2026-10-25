"""Garment Wear Condition Classifier (ResNet-18).

Classifies wear level into: new, gently_used, worn, heavily_worn.
Loaded ONCE at backend startup (Rule #5).
Falls back gracefully to stub mode if weights/condition.pt is absent (Rule #1 & #6).
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
from backend.app.schemas import ConditionAnalysis, ConditionLabel

logger = logging.getLogger("ml.condition")

WEIGHTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "weights" / "condition.pt"

CONDITION_CLASSES: List[ConditionLabel] = ["new", "gently_used", "worn", "heavily_worn"]
_condition_classes: List[str] = list(CONDITION_CLASSES)

# Transform pipeline matching training
_eval_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

_condition_model: Optional[Any] = None
_is_stub_mode: bool = True


def get_condition_classes() -> List[str]:
    """Returns the active condition class label order (from checkpoint or default)."""
    return list(_condition_classes)


def load_condition_model() -> bool:
    """Load trained ResNet-18 condition weights once at startup."""
    global _condition_model, _is_stub_mode, _condition_classes

    if not WEIGHTS_PATH.exists():
        logger.warning(
            f"Weights file not found at '{WEIGHTS_PATH}'. "
            "Garment condition classifier will operate in STUB fallback mode."
        )
        _condition_model = None
        _is_stub_mode = True
        _condition_classes = list(CONDITION_CLASSES)
        return False

    try:
        logger.info(f"Loading condition classifier weights from '{WEIGHTS_PATH}'...")
        # 1. Load checkpoint and extract class names if present
        checkpoint = torch.load(str(WEIGHTS_PATH), map_location="cpu")

        if isinstance(checkpoint, dict) and "class_names" in checkpoint:
            _condition_classes = list(checkpoint["class_names"])
            logger.info(f"Read class order from checkpoint: {_condition_classes}")
        else:
            _condition_classes = list(CONDITION_CLASSES)

        # 2. Build ResNet-18 architecture with matching output classes
        model = resnet18(weights=None)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, len(_condition_classes))

        # 3. Load state dict
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        elif isinstance(checkpoint, dict):
            model.load_state_dict(checkpoint)
        else:
            model = checkpoint

        model.eval()
        _condition_model = model
        _is_stub_mode = False
        logger.info("Successfully loaded condition classifier model (ResNet-18).")
        return True
    except Exception as e:
        logger.error(
            f"Failed to load condition weights from '{WEIGHTS_PATH}': {e}. "
            "Falling back to STUB mode."
        )
        _condition_model = None
        _is_stub_mode = True
        _condition_classes = list(CONDITION_CLASSES)
        return False


def is_using_stub() -> bool:
    return _is_stub_mode


def analyze_condition(
    image_bytes_list: List[bytes],
    confidence_threshold: float = settings.CONFIDENCE_THRESHOLD,
) -> ConditionAnalysis:
    """Classify garment condition from uploaded images.

    Averages predictions across multiple garment images.
    Falls back gracefully to stub if weights are missing.
    """
    # Determine representative image for explainability heatmap
    primary_img_bytes = image_bytes_list[0] if image_bytes_list else b""

    if _is_stub_mode or _condition_model is None:
        heatmap_b64 = generate_gradcam_heatmap(
            model=None,
            target_layer=None,
            image_bytes=primary_img_bytes,
            focus_center=(0.5, 0.45),
        )
        return ConditionAnalysis(
            label="gently_used",
            confidence=0.74,
            heatmap_base64=heatmap_b64,
        )

    # Real ResNet-18 PyTorch inference
    all_probs: List[torch.Tensor] = []

    for img_bytes in image_bytes_list:
        try:
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            tensor = _eval_transforms(image).unsqueeze(0)  # shape (1, 3, 224, 224)
            with torch.no_grad():
                logits = _condition_model(tensor)
                probs = torch.softmax(logits, dim=1).squeeze(0)  # shape (4,)
                all_probs.append(probs)
        except Exception as e:
            logger.warning(f"Error processing image in condition model: {e}")
            continue

    if not all_probs:
        heatmap_b64 = generate_gradcam_heatmap(
            model=None,
            target_layer=None,
            image_bytes=primary_img_bytes,
            focus_center=(0.5, 0.45),
        )
        return ConditionAnalysis(label="gently_used", confidence=0.74, heatmap_base64=heatmap_b64)

    # Average probabilities across all provided photos
    mean_probs = torch.stack(all_probs).mean(dim=0)
    top_idx = int(torch.argmax(mean_probs).item())
    top_prob = float(mean_probs[top_idx].item())
    predicted_label = _condition_classes[top_idx]

    # If top probability falls below configurable threshold, default to conservative wear estimate
    if top_prob < confidence_threshold and predicted_label == "new":
        predicted_label = "gently_used"

    # Compute Grad-CAM heatmap using layer4[-1] of ResNet-18
    target_layer = getattr(_condition_model, "layer4", [None])[-1]
    heatmap_b64 = generate_gradcam_heatmap(
        model=_condition_model,
        target_layer=target_layer,
        image_bytes=primary_img_bytes,
        target_category=top_idx,
        focus_center=(0.5, 0.45),
    )

    return ConditionAnalysis(
        label=predicted_label,
        confidence=round(top_prob, 2),
        heatmap_base64=heatmap_b64,
    )
