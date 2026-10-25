"""Layer A: SQL-Driven Deterministic Eligibility Rules.

Evaluates database tables (PathwayRule, Brand, Facility) to determine
which circular pathways are eligible for a given garment.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models_db import Brand, Facility, PathwayRule
from backend.app.schemas import AnalyzeResponse

# Numerical scale to compare condition levels
CONDITION_HIERARCHY: Dict[str, int] = {
    "new": 4,
    "gently_used": 3,
    "worn": 2,
    "heavily_worn": 1,
}


def check_brand_takeback_eligibility(
    db: Session,
    brand_name: Optional[str],
    material_label: str,
) -> bool:
    """Check brand take-back eligibility against the `brands` table.

    Rule:
    1. Brand name must be present and recognized in DB.
    2. Brand must have `takeback_active == True`.
    3. Brand's `accepted_materials` must match the garment material or be 'all'.
    """
    if not brand_name or not brand_name.strip():
        return False

    clean_brand = brand_name.strip().lower()

    # Query active brands
    brands = db.query(Brand).filter(Brand.takeback_active == True).all()
    matched_brand: Optional[Brand] = None

    for b in brands:
        if b.name.lower() == clean_brand:
            matched_brand = b
            break
        if b.aliases:
            aliases = [a.strip().lower() for a in b.aliases.split(",")]
            if clean_brand in aliases:
                matched_brand = b
                break

    if not matched_brand:
        return False

    # Check material eligibility for brand take-back
    accepted = matched_brand.accepted_materials.lower()
    if accepted == "all":
        return True

    # If material is uncertain, allow takeback if brand accepts general apparel
    if material_label == "uncertain":
        return True

    return material_label.lower() in [m.strip() for m in accepted.split(",")]


def check_recyclability_eligibility(
    db: Session,
    material_label: str,
) -> bool:
    """Check material recyclability against available recycling facilities in DB.

    Rule: At least one recycling facility must accept this material (or 'all').
    Textile recycling is almost universally eligible (graceful fallback).
    """
    recycling_facilities = (
        db.query(Facility).filter(Facility.facility_type == "recycling").all()
    )
    if not recycling_facilities:
        return True  # Fallback to true so user is never blocked

    if material_label == "uncertain":
        return True

    for fac in recycling_facilities:
        acc = fac.accepted_materials.lower()
        if acc == "all" or material_label.lower() in [m.strip() for m in acc.split(",")]:
            return True

    return False


def evaluate_eligibility(
    db: Session,
    analysis: AnalyzeResponse,
) -> Dict[str, bool]:
    """Evaluate eligibility for each circular pathway using SQL rules.

    Returns dict mapping pathway -> is_eligible.
    Never blocks the user; if models fail or tags are missing, degrades gracefully.
    """
    # 1. Load active pathway rules from database table
    rules = db.query(PathwayRule).filter(PathwayRule.is_active == True).all()
    rule_map = {r.pathway: r for r in rules}

    condition_rank = CONDITION_HIERARCHY.get(analysis.condition.label, 1)
    damage_pct = analysis.damage.area_percent
    has_damage = analysis.damage.detected
    material_label = analysis.material.label
    brand_name = analysis.tag.brand

    eligibility: Dict[str, bool] = {}

    # --- 1. Reuse / Resell ---
    reuse_rule = rule_map.get("reuse_resell")
    min_cond_reuse = CONDITION_HIERARCHY.get(
        reuse_rule.min_condition if reuse_rule else "gently_used", 3
    )
    max_dmg_reuse = reuse_rule.max_damage_percent if reuse_rule else 5.0
    eligibility["reuse_resell"] = (condition_rank >= min_cond_reuse) and (damage_pct <= max_dmg_reuse)

    # --- 2. Repair ---
    repair_rule = rule_map.get("repair")
    min_cond_repair = CONDITION_HIERARCHY.get(
        repair_rule.min_condition if repair_rule else "worn", 2
    )
    max_dmg_repair = repair_rule.max_damage_percent if repair_rule else 25.0
    # Must have detected damage, damage area must be repairable (<= max_dmg),
    # and fabric condition must not be disintegrated (>= min_condition)
    eligibility["repair"] = (
        has_damage
        and (damage_pct <= max_dmg_repair)
        and (condition_rank >= min_cond_repair)
    )

    # --- 3. Donate ---
    donate_rule = rule_map.get("donate")
    min_cond_donate = CONDITION_HIERARCHY.get(
        donate_rule.min_condition if donate_rule else "worn", 2
    )
    max_dmg_donate = donate_rule.max_damage_percent if donate_rule else 10.0
    eligibility["donate"] = (condition_rank >= min_cond_donate) and (damage_pct <= max_dmg_donate)

    # --- 4. Recycle ---
    eligibility["recycle"] = check_recyclability_eligibility(db, material_label)

    # --- 5. Brand Take-Back ---
    eligibility["brand_takeback"] = check_brand_takeback_eligibility(
        db=db,
        brand_name=brand_name,
        material_label=material_label,
    )

    return eligibility
