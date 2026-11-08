"""ML Model Loader & Registry.

Loads models ONCE at backend startup (Non-Negotiable Rule #5).
Manages transitioning models from STUB to LOADED as real weights arrive (Rule #1).

Priority order for perception:
  1. Local trained weights (condition/material/damage .pt files in weights/)
  2. VLM API — if VLM_API_KEY is set
  3. Stub — silent fallback, never crashes
"""

import logging
from typing import Any, Dict

try:
    from app.ml.condition import load_condition_model, is_using_stub as condition_is_stub
    from app.ml.damage import load_damage_model, is_using_stub as damage_is_stub
    from app.ml.material import load_material_model, is_using_stub as material_is_stub
    from app.ml.tag.detect import load_tag_detector, is_using_stub as tag_is_stub
    from app.ml.tag.ocr import load_ocr_engine, is_using_stub as ocr_is_stub
except ImportError:
    from backend.app.ml.condition import load_condition_model, is_using_stub as condition_is_stub
    from backend.app.ml.damage import load_damage_model, is_using_stub as damage_is_stub
    from backend.app.ml.material import load_material_model, is_using_stub as material_is_stub
    from backend.app.ml.tag.detect import load_tag_detector, is_using_stub as tag_is_stub
    from backend.app.ml.tag.ocr import load_ocr_engine, is_using_stub as ocr_is_stub

logger = logging.getLogger("ml.loader")


class ModelRegistry:
    _instance = None

    def __init__(self):
        self.is_initialized = False
        self.models_status: Dict[str, str] = {
            "damage_yolo": "stub",
            "condition_resnet": "stub",
            "material_resnet": "stub",
            "tag_detector_yolo": "stub",
            "ocr_paddle": "stub",
            "ranker_xgboost": "stub",
            "vlm": "disabled",
        }
        self.loaded_models: Dict[str, Any] = {}
        self._vlm_provider: str = "none"

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_all_models(self) -> None:
        """Called once during FastAPI lifespan startup."""
        if self.is_initialized:
            return

        logger.info("Initializing ML model registry at startup...")

        # 1. Damage Model (YOLOv8)
        damage_loaded = load_damage_model()
        self.models_status["damage_yolo"] = "loaded" if damage_loaded else "stub"

        # 2. Condition Model (ResNet-18)
        condition_loaded = load_condition_model()
        self.models_status["condition_resnet"] = "loaded" if condition_loaded else "stub"

        # 3. Material Model (ResNet-18)
        material_loaded = load_material_model()
        self.models_status["material_resnet"] = "loaded" if material_loaded else "stub"

        # 4. Tag Detector (YOLOv8) & OCR Engine (PaddleOCR)
        tag_loaded = load_tag_detector()
        self.models_status["tag_detector_yolo"] = "loaded" if tag_loaded else "stub"

        ocr_loaded = load_ocr_engine()
        self.models_status["ocr_paddle"] = "loaded" if ocr_loaded else "stub"

        # 5. XGBoost Ranker (Formula mode)
        self.models_status["ranker_xgboost"] = "stub"

        # 6. VLM client — initialise after local models so priority order is clear
        try:
            from app.ml.vlm import initialize_vlm, vlm_available, vlm_provider_name
        except ImportError:
            from backend.app.ml.vlm import initialize_vlm, vlm_available, vlm_provider_name

        initialize_vlm()
        if vlm_available():
            try:
                from app.config import settings
            except ImportError:
                from backend.app.config import settings
            self.models_status["vlm"] = f"active:{settings.VLM_MODEL}"
            self._vlm_provider = vlm_provider_name()
        else:
            self.models_status["vlm"] = "disabled"
            self._vlm_provider = "none"

        for model_name, status in self.models_status.items():
            logger.info(f"Model [{model_name}] status: {status.upper()}")

        self.is_initialized = True
        logger.info("ML model registry initialization complete.")

    def get_status(self) -> Dict[str, str]:
        return self.models_status

    def get_health_detail(self) -> Dict[str, Any]:
        """Return structured health detail for GET /health/models."""
        try:
            from app.config import settings
        except ImportError:
            from backend.app.config import settings

        local_all_loaded = all(
            self.models_status.get(k) == "loaded"
            for k in ("damage_yolo", "condition_resnet", "material_resnet")
        )

        vlm_status = self.models_status.get("vlm", "disabled")
        vlm_active = vlm_status.startswith("active:")

        if local_all_loaded:
            active_perception = "local"
        elif vlm_active:
            active_perception = "vlm"
        else:
            active_perception = "stub"

        return {
            "models": self.models_status,
            "vlm_provider": self._vlm_provider,
            "vlm_model": settings.VLM_MODEL if vlm_active else None,
            "active_perception": active_perception,
            "perception_priority": ["local_weights", "vlm", "stub"],
        }


model_registry = ModelRegistry.get_instance()
