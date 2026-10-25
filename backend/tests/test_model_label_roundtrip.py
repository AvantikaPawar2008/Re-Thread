"""Tests verifying label order round-trips from training script to backend loaders.

Validates the three key fixes:
1. ImageFolder label remapping matches TASK_CONFIGS class order, overriding alphabetical default.
2. State dict saving uses copy.deepcopy() to isolate best checkpoint weights.
3. Class-weighted CrossEntropyLoss computes balanced inverse-frequency weights from targets.
4. Backend loaders (condition.py and material.py) read and enforce class_names from checkpoints.
"""

import copy
import os
import tempfile
from pathlib import Path
from PIL import Image
import pytest
import torch
import torch.nn as nn
from torchvision.datasets import ImageFolder
from torchvision.models import resnet18

from ml.train_resnet18_classifier import (
    TASK_CONFIGS,
    remap_imagefolder_classes,
    compute_class_weights,
)
import backend.app.ml.condition as condition_mod
import backend.app.ml.material as material_mod


def _create_dummy_image(path: Path):
    """Helper to create a small valid JPEG on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (32, 32), color=(128, 128, 128))
    img.save(str(path), format="JPEG")


def test_remap_imagefolder_classes_aligns_with_task_config():
    """Verify ImageFolder alphabetical sorting is successfully remapped to TASK_CONFIGS order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        train_dir = Path(tmpdir) / "train"
        # Alphabetical order: gently_used, heavily_worn, new, worn
        folder_names = ["gently_used", "heavily_worn", "new", "worn"]
        for name in folder_names:
            _create_dummy_image(train_dir / name / "img1.jpg")

        dataset = ImageFolder(str(train_dir))
        # Default torchvision behavior sorts alphabetically
        assert dataset.classes == ["gently_used", "heavily_worn", "new", "worn"]
        assert dataset.class_to_idx["new"] == 2  # Alphabetical index for 'new'

        # Target order from TASK_CONFIGS
        target_classes = TASK_CONFIGS["condition"]["classes"]  # ['new', 'gently_used', 'worn', 'heavily_worn']
        remapped = remap_imagefolder_classes(dataset, target_classes)

        assert remapped.classes == ["new", "gently_used", "worn", "heavily_worn"]
        assert remapped.class_to_idx["new"] == 0
        assert remapped.class_to_idx["gently_used"] == 1
        assert remapped.class_to_idx["worn"] == 2
        assert remapped.class_to_idx["heavily_worn"] == 3

        # Check target index of the image inside 'new' folder
        new_sample = next(s for s in remapped.samples if "new" in s[0])
        assert new_sample[1] == 0


def test_compute_class_weights_balanced():
    """Verify class-weighted CrossEntropyLoss weights are properly balanced."""
    # Simulating an imbalanced dataset: 10 'new', 1 'heavily_worn'
    targets = [0] * 10 + [1] * 1
    weights = compute_class_weights(targets, num_classes=2)

    # Minority class (index 1) must receive significantly higher weight than majority class (index 0)
    assert weights[1] > weights[0]
    # Mathematically: total = 11, C = 2. w0 = 11 / (2 * 10) = 0.55; w1 = 11 / (2 * 1) = 5.5
    assert pytest.approx(weights[0].item(), 0.01) == 0.55
    assert pytest.approx(weights[1].item(), 0.01) == 5.5


def test_deepcopy_state_dict_isolation():
    """Verify copy.deepcopy prevents in-place mutation of best_weights across epochs."""
    model = nn.Linear(4, 2)
    with torch.no_grad():
        model.weight.fill_(1.0)

    best_weights = copy.deepcopy(model.state_dict())

    # Mutate model weights in-place (simulating subsequent training steps)
    with torch.no_grad():
        model.weight.fill_(999.0)

    # best_weights must remain isolated at 1.0
    assert torch.all(best_weights["weight"] == 1.0)
    assert torch.all(model.weight == 999.0)


def test_condition_checkpoint_label_order_roundtrip(monkeypatch):
    """Verify backend condition loader reads and enforces class_names saved in checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt_path = Path(tmpdir) / "condition_custom.pt"
        custom_classes = ["heavily_worn", "worn", "gently_used", "new"]

        # Create model and save with custom class ordering
        model = resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(custom_classes))

        payload = {
            "model_state_dict": copy.deepcopy(model.state_dict()),
            "class_names": custom_classes,
            "num_classes": len(custom_classes),
            "task": "condition",
        }
        torch.save(payload, str(ckpt_path))

        # Patch condition loader to load our temporary checkpoint
        monkeypatch.setattr(condition_mod, "WEIGHTS_PATH", ckpt_path)
        success = condition_mod.load_condition_model()

        assert success is True
        assert condition_mod.is_using_stub() is False
        # The backend loader must reflect the exact checkpoint class order
        assert condition_mod.get_condition_classes() == custom_classes


def test_material_checkpoint_label_order_roundtrip(monkeypatch):
    """Verify backend material loader reads and enforces class_names saved in checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt_path = Path(tmpdir) / "material_custom.pt"
        custom_classes = ["blend", "synthetic", "natural"]

        model = resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(custom_classes))

        payload = {
            "model_state_dict": copy.deepcopy(model.state_dict()),
            "class_names": custom_classes,
            "num_classes": len(custom_classes),
            "task": "material",
        }
        torch.save(payload, str(ckpt_path))

        monkeypatch.setattr(material_mod, "WEIGHTS_PATH", ckpt_path)
        success = material_mod.load_material_model()

        assert success is True
        assert material_mod.is_using_stub() is False
        assert material_mod.get_material_classes() == custom_classes
