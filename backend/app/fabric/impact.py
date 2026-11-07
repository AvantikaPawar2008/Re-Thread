"""Sustainability impact estimates with explicit, documented assumptions.

This module deliberately reports *less* than it could. It only counts things
the user actually did (completed projects) and multiplies by clearly labelled
assumed weights. Carbon and water figures are produced **only** if a verified
factor with a source citation is configured in ``data/impact_assumptions.json``;
the default configuration ships with none, so none are reported.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

from app.fabric import recommender

DATA_FILE = Path(__file__).resolve().parent / "data" / "impact_assumptions.json"

WEIGHT_USER = "user"
WEIGHT_CATEGORY = "assumed_category"
WEIGHT_DEFAULT = "assumed_default"


@lru_cache(maxsize=1)
def load_assumptions() -> Dict[str, Any]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_weight(
    category_key: Optional[str], user_weight_kg: Optional[float] = None
) -> Tuple[float, str]:
    """Return ``(weight_kg, source)`` for a garment.

    A user-supplied weight wins if it is a sensible positive number.
    """
    cfg = load_assumptions()
    if user_weight_kg is not None:
        try:
            w = float(user_weight_kg)
        except (TypeError, ValueError):
            w = 0.0
        if 0 < w <= float(cfg["max_user_weight_kg"]):
            return round(w, 3), WEIGHT_USER
    cats = recommender.list_categories()
    if category_key and category_key in cats:
        return float(cats[category_key]["typical_weight_kg"]), WEIGHT_CATEGORY
    return float(cfg["default_garment_weight_kg"]), WEIGHT_DEFAULT


def environmental_factors_enabled() -> bool:
    f = load_assumptions().get("environmental_factors", {})
    return bool(
        f.get("enabled")
        and f.get("source")
        and f.get("co2e_kg_per_kg") is not None
        and f.get("water_litres_per_kg") is not None
    )


def summarize(
    *,
    analyses_count: int,
    saved_ideas_count: int,
    projects: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Aggregate a user's impact.

    ``projects`` items need ``weight_kg`` and ``weight_source``.
    """
    plist = list(projects)
    total = sum(float(p["weight_kg"]) for p in plist)
    user_kg = sum(float(p["weight_kg"]) for p in plist if p["weight_source"] == WEIGHT_USER)
    assumed_kg = total - user_kg

    cfg = load_assumptions()
    factors = cfg.get("environmental_factors", {})
    env: Dict[str, Any]
    if environmental_factors_enabled():
        env = {
            "status": "configured",
            "co2e_kg": round(total * float(factors["co2e_kg_per_kg"]), 2),
            "water_litres": round(total * float(factors["water_litres_per_kg"]), 0),
            "source": factors["source"],
            "label": "Indicative estimate from the configured factor; not a measurement.",
        }
    else:
        env = {
            "status": "not_configured",
            "co2e_kg": None,
            "water_litres": None,
            "source": None,
            "label": factors.get("explanation", "Not estimated."),
        }

    return {
        "analyses_count": int(analyses_count),
        "saved_ideas_count": int(saved_ideas_count),
        "completed_projects_count": len(plist),
        "garments_reused_estimate": len(plist),
        "fabric_kg_diverted_upper_bound": round(total, 2),
        "fabric_kg_from_user_weights": round(user_kg, 2),
        "fabric_kg_from_assumed_weights": round(assumed_kg, 2),
        "environmental": env,
        "assumptions": list(cfg["assumptions"]),
        "is_estimate": True,
    }