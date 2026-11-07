"""Verified-accuracy reports.

Confidence (a softmax probability) and accuracy (how often the model is right
on data it never trained on) are different things. The only accuracy this
application ever shows comes from an evaluation report written by
``ml/evaluate_fabric_models.py``, and only when that report was computed for
the **exact weights file currently loaded** (matched by SHA-256) and the same
class list. Anything else is reported as "no verified accuracy".
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

logger = logging.getLogger("fabric.metrics")


def file_sha256(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def read_report(path: Path) -> Optional[Dict[str, Any]]:
    """Read the evaluation report, or ``None`` if absent/unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        logger.warning("Evaluation report is unreadable; ignoring it.")
        return None
    return data if isinstance(data, dict) else None


def verified_summary(
    report: Optional[Dict[str, Any]],
    model_key: str,
    loaded_sha256: Optional[str],
    loaded_class_names: Sequence[str],
) -> Optional[Dict[str, Any]]:
    """Return a small, display-safe summary or ``None`` when it cannot be trusted."""
    if not report or not loaded_sha256:
        return None
    entry = (report.get("models") or {}).get(model_key)
    if not isinstance(entry, dict):
        return None
    if entry.get("checkpoint_sha256") != loaded_sha256:
        return None  # report is for different weights
    if list(report.get("class_names") or []) != list(loaded_class_names):
        return None  # report is for a different class list
    try:
        return {
            "accuracy": float(entry["accuracy"]),
            "macro_f1": float(entry["macro_f1"]),
            "n_test_images": int(report["test_set"]["n"]),
            "evaluated_at": str(report.get("generated_at", "")),
            "note": "Measured on a held-out test set that was not used for training.",
        }
    except (KeyError, TypeError, ValueError):
        return None


def agreement_summary(
    report: Optional[Dict[str, Any]],
    sha_by_model: Dict[str, Optional[str]],
) -> Optional[Dict[str, Any]]:
    """Agreement statistics, only if the report covers both loaded weight files."""
    if not report:
        return None
    ag = report.get("agreement")
    models = report.get("models") or {}
    if not isinstance(ag, dict):
        return None
    for key in ("resnet50", "nasnet"):
        entry = models.get(key)
        if not isinstance(entry, dict) or entry.get("checkpoint_sha256") != sha_by_model.get(key):
            return None
    try:
        return {
            "agreement_rate": float(ag["agreement_rate"]),
            "accuracy_when_agree": (
                None if ag.get("accuracy_when_agree") is None else float(ag["accuracy_when_agree"])
            ),
            "accuracy_when_disagree_resnet50": ag.get("accuracy_when_disagree_resnet50"),
            "accuracy_when_disagree_nasnet": ag.get("accuracy_when_disagree_nasnet"),
        }
    except (KeyError, TypeError, ValueError):
        return None