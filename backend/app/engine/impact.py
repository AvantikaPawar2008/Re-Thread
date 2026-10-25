"""Layer C: Climate Impact Calculator based on Cited LCA Lookup Factors.

Computes estimated water (litres) and CO2 (kg) saved by multiplying
per-kg lifecycle factors from `impact_factors` table by garment weight (default 0.3 kg).
Handles 'uncertain' material by using benchmark textile blend averages.
"""

from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models_db import ImpactFactor
from backend.app.schemas import ImpactEstimate


def calculate_impact(
    db: Session,
    pathway: str,
    material_label: str,
    garment_weight_kg: float = 0.3,
) -> ImpactEstimate:
    """Calculate water (litres) and CO2 (kg) saved based on published LCA factors.

    If material is 'uncertain', defaults to 'blend' (conservative circular baseline).
    """
    weight = garment_weight_kg if garment_weight_kg and garment_weight_kg > 0 else settings.DEFAULT_GARMENT_WEIGHT_KG

    # Map material to one of the 3 factor keys
    if material_label in ("natural", "synthetic", "blend"):
        mat_key = material_label
    else:
        # For 'uncertain', use 'blend' as representative average factor
        mat_key = "blend"

    factor = (
        db.query(ImpactFactor)
        .filter(
            ImpactFactor.pathway == pathway,
            ImpactFactor.material_type == mat_key,
        )
        .first()
    )

    if not factor:
        # Fallback to any factor for this pathway
        factor = db.query(ImpactFactor).filter(ImpactFactor.pathway == pathway).first()

    if factor:
        water_saved = round(factor.water_litres_saved_per_kg * weight, 1)
        co2_saved = round(factor.co2_kg_saved_per_kg * weight, 2)
    else:
        # General textile conservative baseline if table has missing pathway
        water_saved = round(2500.0 * weight, 1)
        co2_saved = round(8.0 * weight, 2)

    return ImpactEstimate(
        water_litres_saved=water_saved,
        co2_kg_saved=co2_saved,
    )
