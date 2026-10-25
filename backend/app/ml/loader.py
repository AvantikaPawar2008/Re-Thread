"""ML Model Loader & Registry.

Loads models ONCE at backend startup (Non-Negotiable Rule #5).
Manages transitioning models from STUB to LOADED as real weights arrive (Rule #1).
"""

import logging
from typing import Dict, Any

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
        }
        self.loaded_models: Dict[str, Any] = {}

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

        for model_name, status in self.models_status.items():
            logger.info(f"Model [{model_name}] status: {status.upper()}")

        self.is_initialized = True
        logger.info("ML model registry initialization complete.")

    def get_status(self) -> Dict[str, str]:
        return self.models_status


model_registry = ModelRegistry.get_instance()
