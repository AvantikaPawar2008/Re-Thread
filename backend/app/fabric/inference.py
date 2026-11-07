"""ResNet50 and NASNet inference behind one interface.

* Models are loaded **once** at application startup into a registry.
* Checkpoints are self-describing (architecture, class names, preprocessing),
  loaded with ``weights_only=True`` so unpickling cannot execute code.
* If weights are missing, unreadable or inconsistent, that model is reported
  as unavailable with a reason. There is **no fallback to fake output**: a
  model that is not available contributes nothing, and if neither is available
  the API returns an explicit "models unavailable" error.
* PyTorch is imported lazily so the module (and the whole API) starts even
  when torch is not installed; the models then simply report ``error``.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from app.fabric import architectures as arch_mod
from app.fabric import metrics as metrics_mod
from app.fabric.decision import Prediction
from app.fabric.errors import ModelsUnavailable

logger = logging.getLogger("fabric.inference")

MODEL_KEYS = (arch_mod.ARCH_RESNET50, arch_mod.ARCH_NASNET)

STATE_LOADED = "loaded"
STATE_MISSING = "missing"
STATE_ERROR = "error"

REASON_NOT_TRAINED = (
    "No trained weights are installed for this model. Train it with "
    "ml/train_fabric_classifiers.py (see the README)."
)

ModelBuilder = Callable[..., Any]


@dataclass
class ModelStatus:
    key: str
    state: str                       # loaded | missing | error
    reason: Optional[str] = None     # user-safe explanation when not loaded
    architecture: Optional[str] = None
    num_classes: Optional[int] = None
    class_names: List[str] = field(default_factory=list)
    checkpoint_sha256: Optional[str] = None

    @property
    def available(self) -> bool:
        return self.state == STATE_LOADED


@dataclass
class _Loaded:
    key: str
    timm_name: Optional[str]
    class_names: List[str]
    preprocess: Dict[str, Any]
    model: Any
    transform: Any
    sha256: str
    train_info: Dict[str, Any]


@dataclass
class ModelRun:
    """Outcome of attempting one model on one image."""

    key: str
    architecture: str
    available: bool
    prediction: Optional[Prediction] = None
    latency_ms: Optional[float] = None
    reason: Optional[str] = None


class FabricModelRegistry:
    def __init__(
        self,
        weights_dir: Path,
        filenames: Mapping[str, str],
        metrics_file: Optional[str] = None,
        *,
        builder: Optional[ModelBuilder] = None,
    ):
        self._dir = Path(weights_dir)
        self._filenames = dict(filenames)
        self._metrics_path = (self._dir / metrics_file) if metrics_file else None
        # Injectable so tests can substitute a tiny network. Production uses the
        # real architectures.
        self._builder: ModelBuilder = builder or arch_mod.build_model
        self._models: Dict[str, _Loaded] = {}
        self._status: Dict[str, ModelStatus] = {
            k: ModelStatus(k, STATE_MISSING, REASON_NOT_TRAINED, arch_mod.display_name(k))
            for k in MODEL_KEYS
        }
        self._report: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self.loaded_once = False

    # ------------------------------------------------------------------ load
    def load_all(self) -> None:
        """Load every available checkpoint. Never raises."""
        with self._lock:
            self._models.clear()
            for key in MODEL_KEYS:
                self._load_one(key)
            self._reconcile_class_lists()
            self._report = (
                metrics_mod.read_report(self._metrics_path) if self._metrics_path else None
            )
            self.loaded_once = True
        for key, st in self._status.items():
            logger.info("Fabric model [%s]: %s%s", key, st.state, f" ({st.reason})" if st.reason else "")

    def _load_one(self, key: str) -> None:
        path = self._dir / self._filenames[key]
        if not path.is_file():
            logger.warning("Fabric weights for %s not found at %s", key, path)
            self._status[key] = ModelStatus(key, STATE_MISSING, REASON_NOT_TRAINED, arch_mod.display_name(key))
            return
        try:
            import torch  # noqa: WPS433 (lazy on purpose)
        except ImportError:
            self._status[key] = ModelStatus(
                key, STATE_ERROR, "PyTorch is not installed on the server.", arch_mod.display_name(key)
            )
            return

        try:
            ckpt = torch.load(str(path), map_location="cpu", weights_only=True)
            if not isinstance(ckpt, dict):
                raise ValueError("checkpoint is not a dictionary")
            if ckpt.get("format_version") != arch_mod.CHECKPOINT_FORMAT_VERSION:
                raise ValueError("unsupported checkpoint format version")
            if ckpt.get("arch") != key:
                raise ValueError(f"checkpoint architecture {ckpt.get('arch')!r} != expected {key!r}")
            class_names = [str(c) for c in ckpt["class_names"]]
            if len(class_names) < 2 or len(set(class_names)) != len(class_names):
                raise ValueError("invalid class_names")
            preprocess = dict(ckpt["preprocess"])
            arch_mod.validate_preprocess(preprocess)
            timm_name = ckpt.get("timm_name")

            model = self._builder(key, len(class_names), timm_name=timm_name, pretrained=False)
            model.load_state_dict(ckpt["model_state_dict"], strict=True)
            model.eval()
            transform = arch_mod.build_eval_transform(preprocess)
            sha = metrics_mod.file_sha256(path)

            self._models[key] = _Loaded(
                key=key,
                timm_name=timm_name,
                class_names=class_names,
                preprocess=preprocess,
                model=model,
                transform=transform,
                sha256=sha,
                train_info=dict(ckpt.get("train_info") or {}),
            )
            self._status[key] = ModelStatus(
                key,
                STATE_LOADED,
                None,
                arch_mod.display_name(key, timm_name),
                len(class_names),
                class_names,
                sha,
            )
        except Exception:  # noqa: BLE001 - never crash startup over one checkpoint
            logger.exception("Failed to load fabric weights for %s from %s", key, path)
            self._status[key] = ModelStatus(
                key,
                STATE_ERROR,
                "The trained weights could not be loaded (corrupt or incompatible checkpoint).",
                arch_mod.display_name(key),
            )

    def _reconcile_class_lists(self) -> None:
        """Both models must share one class mapping, or they cannot be compared."""
        a, b = self._models.get(MODEL_KEYS[0]), self._models.get(MODEL_KEYS[1])
        if a and b and a.class_names != b.class_names:
            logger.error(
                "ResNet50 and NASNet checkpoints use different class lists; "
                "disabling NASNet so predictions are never compared across mappings."
            )
            del self._models[MODEL_KEYS[1]]
            self._status[MODEL_KEYS[1]] = ModelStatus(
                MODEL_KEYS[1],
                STATE_ERROR,
                "Disabled: its class list differs from the ResNet50 checkpoint. "
                "Retrain both models on the same dataset.",
                arch_mod.display_name(MODEL_KEYS[1], b.timm_name),
            )

    # ---------------------------------------------------------------- status
    def status(self) -> Dict[str, ModelStatus]:
        return dict(self._status)

    def any_available(self) -> bool:
        return bool(self._models)

    def class_names(self) -> List[str]:
        for key in MODEL_KEYS:
            if key in self._models:
                return list(self._models[key].class_names)
        return []

    def model_versions(self) -> Dict[str, Optional[str]]:
        return {k: (self._models[k].sha256[:12] if k in self._models else None) for k in MODEL_KEYS}

    def verified_metrics(self) -> Dict[str, Any]:
        """Verified accuracy per model + agreement stats (or ``None`` when unverifiable)."""
        out: Dict[str, Any] = {}
        sha_by_model = {k: (self._models[k].sha256 if k in self._models else None) for k in MODEL_KEYS}
        for key in MODEL_KEYS:
            loaded = self._models.get(key)
            out[key] = metrics_mod.verified_summary(
                self._report, key, loaded.sha256 if loaded else None,
                loaded.class_names if loaded else [],
            )
        out["agreement"] = metrics_mod.agreement_summary(self._report, sha_by_model)
        return out

    # --------------------------------------------------------------- predict
    def predict(self, image, top_k: int = 3) -> List[ModelRun]:
        """Run every available model on a PIL RGB image.

        Returns one :class:`ModelRun` per known model (available or not).
        Raises :class:`ModelsUnavailable` when no model is loaded at all.
        """
        if not self._models:
            raise ModelsUnavailable(
                "No trained models are available, so this image cannot be analysed. "
                "The site administrator needs to train or install the ResNet50 and NASNet weights.",
            )
        runs: List[ModelRun] = []
        for key in MODEL_KEYS:
            loaded = self._models.get(key)
            st = self._status[key]
            if loaded is None:
                runs.append(ModelRun(key, st.architecture or key, False, reason=st.reason))
                continue
            arch_name = arch_mod.display_name(key, loaded.timm_name)
            try:
                t0 = time.perf_counter()
                probs = self._forward(loaded, image)
                latency = (time.perf_counter() - t0) * 1000.0
                runs.append(
                    ModelRun(
                        key, arch_name, True,
                        prediction=_to_prediction(key, loaded.class_names, probs, top_k),
                        latency_ms=round(latency, 1),
                    )
                )
            except Exception:  # noqa: BLE001
                logger.exception("Inference failed for %s", key)
                runs.append(ModelRun(key, arch_name, False, reason="This model failed while analysing the image."))
        if not any(r.available for r in runs):
            raise ModelsUnavailable("The models failed to analyse this image. Please try again or use a different photo.")
        return runs

    @staticmethod
    def _forward(loaded: _Loaded, image) -> Sequence[float]:
        import torch

        tensor = loaded.transform(image.convert("RGB")).unsqueeze(0)
        with torch.inference_mode():
            logits = loaded.model(tensor)
            probs = torch.softmax(logits.float(), dim=1).squeeze(0)
        return probs.tolist()


def _to_prediction(key: str, class_names: List[str], probs: Sequence[float], top_k: int) -> Prediction:
    if len(probs) != len(class_names):
        raise ValueError("model output size does not match class list")
    order = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
    top = tuple((class_names[i], round(float(probs[i]), 6)) for i in order[: max(1, top_k)])
    best = order[0]
    return Prediction(model=key, label=class_names[best], confidence=float(probs[best]), top_k=top)