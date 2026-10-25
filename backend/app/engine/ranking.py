"""Layer B: Decision Ranking Layer with Ranker Interface.

Defines a BaseRanker abstract interface and a transparent WeightedFormulaRanker
implementation. This allows XGBoost (or LightGBM) to drop in as an alternative
ranker implementation without modifying caller contracts (Non-Negotiable Rule #4).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, NamedTuple, Optional, Tuple
from backend.app.schemas import AnalyzeResponse

CONDITION_WEIGHTS: Dict[str, float] = {
    "new": 1.0,
    "gently_used": 0.8,
    "worn": 0.5,
    "heavily_worn": 0.2,
}

MATERIAL_WEIGHTS: Dict[str, float] = {
    "natural": 0.85,
    "blend": 0.70,
    "synthetic": 0.60,
    "uncertain": 0.50,
}


class RankedScore(NamedTuple):
    pathway: str
    score: float
    eligible: bool


class BaseRanker(ABC):
    """Abstract interface for circular pathway ranking."""

    @abstractmethod
    def rank(
        self,
        analysis: AnalyzeResponse,
        eligibility: Dict[str, bool],
        distances: Dict[str, float],
    ) -> Tuple[List[RankedScore], Dict[str, float]]:
        """Rank pathways and return (ranked_scores, shap_feature_attributions)."""
        pass


class WeightedFormulaRanker(BaseRanker):
    """Transparent, deterministic weighted scoring formula ranker.

    Computes normalized suitability scores (0.0 to 1.0) for each eligible
    pathway and returns SHAP-style feature attributions for explainability.
    """

    def rank(
        self,
        analysis: AnalyzeResponse,
        eligibility: Dict[str, bool],
        distances: Dict[str, float],
    ) -> Tuple[List[RankedScore], Dict[str, float]]:
        cond_w = CONDITION_WEIGHTS.get(analysis.condition.label, 0.5)
        mat_w = MATERIAL_WEIGHTS.get(analysis.material.label, 0.5)
        dmg_pct = analysis.damage.area_percent
        has_damage = analysis.damage.detected
        has_brand = bool(analysis.tag.brand and analysis.tag.brand.strip())

        raw_scores: Dict[str, float] = {}
        # Track feature contributions for the winning pathway
        feature_impacts: Dict[str, Dict[str, float]] = {}

        # ------------------------------------------------------------------
        # 1. Repair: Top choice when damage is present and within repairable limit
        # ------------------------------------------------------------------
        if eligibility.get("repair", False) and has_damage:
            dmg_factor = max(0.0, 0.40 - (dmg_pct * 0.015))
            cond_factor = 0.20 * cond_w
            mat_factor = 0.15 * mat_w
            brand_factor = 0.05 if has_brand else 0.0
            repair_base = 0.20 + dmg_factor + cond_factor + mat_factor + brand_factor
            raw_scores["repair"] = max(0.20, min(0.95, repair_base))
            feature_impacts["repair"] = {
                "material": round(mat_factor, 2),
                "condition": round(cond_factor, 2),
                "damage_percent": round(dmg_factor, 2),
                "brand": round(brand_factor, 2),
            }
        else:
            raw_scores["repair"] = 0.12
            feature_impacts["repair"] = {
                "material": 0.05,
                "condition": 0.05,
                "damage_percent": -0.25,
                "brand": 0.0,
            }

        # ------------------------------------------------------------------
        # 2. Reuse / Resell: Best for garments with minimal damage & high condition
        # ------------------------------------------------------------------
        if eligibility.get("reuse_resell", False):
            cond_factor = 0.45 * cond_w
            dmg_penalty = -(dmg_pct * 0.06)
            mat_factor = 0.15 * mat_w
            brand_factor = 0.10 if has_brand else 0.0
            reuse_base = 0.25 + cond_factor + dmg_penalty + mat_factor + brand_factor
            raw_scores["reuse_resell"] = max(0.20, min(0.96, reuse_base))
            feature_impacts["reuse_resell"] = {
                "material": round(mat_factor, 2),
                "condition": round(cond_factor, 2),
                "damage_percent": round(dmg_penalty, 2),
                "brand": round(brand_factor, 2),
            }
        else:
            raw_scores["reuse_resell"] = 0.10
            feature_impacts["reuse_resell"] = {
                "material": 0.05,
                "condition": -0.20,
                "damage_percent": -0.20,
                "brand": 0.0,
            }

        # ------------------------------------------------------------------
        # 3. Donate: High for wearable everyday clothes in clean condition
        # ------------------------------------------------------------------
        if eligibility.get("donate", False):
            cond_factor = 0.35 * cond_w
            dmg_factor = max(-0.15, -(dmg_pct * 0.03))
            mat_factor = 0.15 * mat_w
            donate_base = 0.30 + cond_factor + dmg_factor + mat_factor
            raw_scores["donate"] = max(0.20, min(0.90, donate_base))
            feature_impacts["donate"] = {
                "material": round(mat_factor, 2),
                "condition": round(cond_factor, 2),
                "damage_percent": round(dmg_factor, 2),
                "brand": 0.0,
            }
        else:
            raw_scores["donate"] = 0.12
            feature_impacts["donate"] = {
                "material": 0.05,
                "condition": -0.15,
                "damage_percent": -0.20,
                "brand": 0.0,
            }

        # ------------------------------------------------------------------
        # 4. Brand Take-Back: High for eligible brand partners
        # ------------------------------------------------------------------
        if eligibility.get("brand_takeback", False):
            brand_factor = 0.35
            cond_factor = 0.20 * cond_w
            mat_factor = 0.15 * mat_w
            raw_scores["brand_takeback"] = max(0.30, min(0.92, 0.20 + brand_factor + cond_factor + mat_factor))
            feature_impacts["brand_takeback"] = {
                "material": round(mat_factor, 2),
                "condition": round(cond_factor, 2),
                "damage_percent": 0.0,
                "brand": round(brand_factor, 2),
            }
        else:
            raw_scores["brand_takeback"] = 0.05
            feature_impacts["brand_takeback"] = {
                "material": 0.0,
                "condition": 0.0,
                "damage_percent": 0.0,
                "brand": -0.30,
            }

        # ------------------------------------------------------------------
        # 5. Recycle: High when wear is heavy or damage is extensive
        # ------------------------------------------------------------------
        if cond_w <= 0.3 or dmg_pct > 20.0:
            recycle_base = 0.85
            feature_impacts["recycle"] = {
                "material": 0.20,
                "condition": -0.30,
                "damage_percent": 0.35,
                "brand": 0.0,
            }
        else:
            recycle_base = 0.30 + (0.01 * dmg_pct)
            feature_impacts["recycle"] = {
                "material": round(0.10 * mat_w, 2),
                "condition": round(-0.10 * cond_w, 2),
                "damage_percent": round(0.01 * dmg_pct, 2),
                "brand": 0.0,
            }
        raw_scores["recycle"] = max(0.15, min(0.95, recycle_base))

        # ------------------------------------------------------------------
        # Distance modulation (Layer C integration)
        # Closer drop-off facilities receive a modest bonus (+0.05 to -0.08)
        # ------------------------------------------------------------------
        final_list: List[RankedScore] = []
        for pathway, base_score in raw_scores.items():
            is_elig = eligibility.get(pathway, False)
            dist = distances.get(pathway, 15.0)

            # Distance bonus/penalty formula
            dist_mod = max(-0.08, min(0.05, 0.05 - (dist * 0.005)))
            score = base_score + dist_mod

            # If pathway is ruled ineligible by Layer A, penalize score below eligible options
            if not is_elig:
                score = min(score, 0.15)

            score = round(max(0.01, min(0.99, score)), 2)
            final_list.append(RankedScore(pathway=pathway, score=score, eligible=is_elig))

        # Sort descending by score
        final_list.sort(key=lambda x: x.score, reverse=True)

        # Select SHAP attribution for top pathway
        winning_pathway = final_list[0].pathway
        shap_attribution = feature_impacts.get(
            winning_pathway,
            {"material": 0.20, "condition": 0.25, "damage_percent": 0.10, "brand": 0.05},
        )

        return final_list, shap_attribution


# Singleton ranker instances
_formula_ranker = WeightedFormulaRanker()
_xgb_ranker = None


def get_ranker() -> BaseRanker:
    """Return configured ranker implementation (XGBoost or WeightedFormula)."""
    global _xgb_ranker
    from backend.app.config import settings

    if getattr(settings, "RANKER_TYPE", "formula") == "xgboost":
        if _xgb_ranker is None:
            try:
                from backend.app.engine.xgb_ranker import XGBoostRanker
                _xgb_ranker = XGBoostRanker()
            except Exception:
                return _formula_ranker
        return _xgb_ranker
    return _formula_ranker


def rank_pathways(
    analysis: AnalyzeResponse,
    eligibility: Dict[str, bool],
    distances: Dict[str, float],
    ranker: Optional[BaseRanker] = None,
) -> Tuple[List[Tuple[str, float, bool]], Dict[str, float]]:
    """Public wrapper adhering to the engine contract."""
    active_ranker = ranker if ranker is not None else get_ranker()
    ranked_scores, shap = active_ranker.rank(analysis, eligibility, distances)
    return [(s.pathway, s.score, s.eligible) for s in ranked_scores], shap
