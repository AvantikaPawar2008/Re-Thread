"""Single source of truth for model architectures and preprocessing.

Both the training script (``ml/train_fabric_classifiers.py``) and the serving
registry (``inference.py``) build networks and image transforms from here, so
what the model saw during training is by construction what it sees at serving
time. The preprocessing used is also stored *inside* every checkpoint, and the
server uses the checkpoint's copy.

PyTorch / torchvision / timm are imported lazily inside functions so that
importing this module never requires them.

NASNet variants
---------------
torchvision does not ship NASNet. The PyTorch image-model library ``timm``
provides ``nasnetalarge`` (roughly 89 M parameters, 331x331 input). NASNet-Mobile
is, to the best of my knowledge, available in Keras/TensorFlow
(``tf.keras.applications.NASNetMobile``) and in the third-party
``pretrainedmodels`` package rather than in timm or torchvision. THIS WAS NOT
VERIFIED in the development environment (no package access), so check
``timm.list_models('*nasnet*')`` on your machine. To stay inside the
repository's PyTorch stack the default is ``nasnetalarge``. The variant is
configurable (``--nasnet-name`` when training) and is recorded in the
checkpoint, so serving always rebuilds exactly what was trained. If your timm
exposes a smaller NASNet, pass its name and no other code changes are needed.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

ARCH_RESNET50 = "resnet50"
ARCH_NASNET = "nasnet"
ARCH_CHOICES = (ARCH_RESNET50, ARCH_NASNET)

DEFAULT_NASNET_TIMM_NAME = "nasnetalarge"

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

CHECKPOINT_FORMAT_VERSION = 1


def display_name(arch: str, timm_name: Optional[str] = None) -> str:
    if arch == ARCH_RESNET50:
        return "ResNet50"
    if arch == ARCH_NASNET:
        return f"NASNet ({timm_name or DEFAULT_NASNET_TIMM_NAME})"
    return arch


def build_model(
    arch: str,
    num_classes: int,
    *,
    timm_name: Optional[str] = None,
    pretrained: bool = False,
):
    """Build an (untrained or ImageNet-pretrained) classifier with ``num_classes`` outputs."""
    if num_classes < 2:
        raise ValueError("num_classes must be at least 2")

    if arch == ARCH_RESNET50:
        import torch.nn as nn
        from torchvision.models import ResNet50_Weights, resnet50

        model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2 if pretrained else None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model

    if arch == ARCH_NASNET:
        import timm

        name = timm_name or DEFAULT_NASNET_TIMM_NAME
        available = set(timm.list_models("*nasnet*"))
        if name not in available:
            raise ValueError(
                f"NASNet variant '{name}' is not available in the installed timm "
                f"({sorted(available) or 'no NASNet models found'})."
            )
        return timm.create_model(name, pretrained=pretrained, num_classes=num_classes)

    raise ValueError(f"Unknown architecture '{arch}'. Choose one of {ARCH_CHOICES}.")


def resolve_preprocess(arch: str, model=None) -> Dict[str, Any]:
    """Preprocessing parameters for an architecture (stored in the checkpoint)."""
    if arch == ARCH_RESNET50:
        return {
            "input_size": 224,
            "resize_size": 256,
            "mean": list(IMAGENET_MEAN),
            "std": list(IMAGENET_STD),
            "interpolation": "bilinear",
        }
    if arch == ARCH_NASNET:
        if model is None:
            raise ValueError("A model instance is required to resolve NASNet preprocessing.")
        from timm.data import resolve_data_config

        cfg = resolve_data_config({}, model=model)
        _, h, _w = cfg["input_size"]
        crop_pct = float(cfg.get("crop_pct") or 0.875)
        return {
            "input_size": int(h),
            "resize_size": int(math.floor(h / crop_pct)),
            "mean": [float(x) for x in cfg["mean"]],
            "std": [float(x) for x in cfg["std"]],
            "interpolation": str(cfg.get("interpolation", "bicubic")),
        }
    raise ValueError(f"Unknown architecture '{arch}'.")


def validate_preprocess(p: Dict[str, Any]) -> None:
    try:
        ok = (
            int(p["input_size"]) >= 32
            and int(p["resize_size"]) >= int(p["input_size"])
            and len(p["mean"]) == 3
            and len(p["std"]) == 3
            and all(float(s) > 0 for s in p["std"])
        )
    except (KeyError, TypeError, ValueError):
        ok = False
    if not ok:
        raise ValueError("Checkpoint contains invalid preprocessing parameters.")


def _interp(name: str):
    from torchvision.transforms import InterpolationMode

    return {
        "bicubic": InterpolationMode.BICUBIC,
        "bilinear": InterpolationMode.BILINEAR,
    }.get(str(name).lower(), InterpolationMode.BILINEAR)


def build_eval_transform(p: Dict[str, Any]):
    """Deterministic transform used for validation, test and serving."""
    import torchvision.transforms as T

    validate_preprocess(p)
    return T.Compose(
        [
            T.Resize(int(p["resize_size"]), interpolation=_interp(p.get("interpolation", "bilinear"))),
            T.CenterCrop(int(p["input_size"])),
            T.ToTensor(),
            T.Normalize(list(p["mean"]), list(p["std"])),
        ]
    )


def build_train_transform(p: Dict[str, Any]):
    """Augmentation applied to TRAINING images only (never to val/test)."""
    import torchvision.transforms as T

    validate_preprocess(p)
    return T.Compose(
        [
            T.RandomResizedCrop(
                int(p["input_size"]),
                scale=(0.6, 1.0),
                interpolation=_interp(p.get("interpolation", "bilinear")),
            ),
            T.RandomHorizontalFlip(),
            T.RandomRotation(15),
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
            T.ToTensor(),
            T.Normalize(list(p["mean"]), list(p["std"])),
        ]
    )


def checkpoint_payload(
    *,
    arch: str,
    timm_name: Optional[str],
    class_names: List[str],
    preprocess: Dict[str, Any],
    state_dict,
    train_info: Dict[str, Any],
) -> Dict[str, Any]:
    """The self-describing checkpoint structure (only tensors, lists, str, numbers)."""
    return {
        "format_version": CHECKPOINT_FORMAT_VERSION,
        "arch": arch,
        "timm_name": timm_name,
        "class_names": list(class_names),
        "preprocess": preprocess,
        "model_state_dict": state_dict,
        "train_info": train_info,
    }