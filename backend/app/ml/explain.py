"""Explainable AI (SHAP & Grad-CAM) Stub.

Generates feature attribution (SHAP TreeExplainer) and visual heatmaps (Grad-CAM).
"""

from typing import Dict, Any


def get_ranking_shap_attributions(
    material: str,
    condition: str,
    damage_percent: float,
    brand: str | None,
) -> Dict[str, float]:
    """Compute feature impact scores for the top recommendation using SHAP.

    Stub returns values matching Section 11 structure.
    """
    # Realistic relative importance
    return {
        "material": 0.25,
        "condition": 0.35,
        "damage_percent": -0.15,
        "brand": 0.10 if brand else 0.0,
    }
