"""Endpoint: POST /recommend

Takes garment analysis and user coordinates to evaluate eligibility (Layer A),
rank pathways with SHAP feature attributions (Layer B), look up nearest partners
and compute climate impact (Layer C), generate plain-language explanations,
and issue a lifecycle QR tracking code.
"""

import json
from typing import Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db import get_db
from backend.app.engine.explanation import generate_explanation
from backend.app.engine.geography import find_nearest_partner
from backend.app.engine.impact import calculate_impact
from backend.app.engine.qr import generate_qr_id
from backend.app.engine.ranking import rank_pathways
from backend.app.engine.rules import evaluate_eligibility
from backend.app.models_db import Recommendation
from backend.app.schemas import (
    RecommendRequest,
    RecommendResponse,
    RankedPathway,
)

router = APIRouter()


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend ranked pathways for an analyzed garment",
    description="Applies hybrid decision engine (rules + ranking + geography + impact) to suggest circular options.",
)
def recommend_pathways(
    payload: RecommendRequest,
    db: Session = Depends(get_db),
) -> RecommendResponse:
    analysis = payload.analysis
    user_lat = payload.user_latitude
    user_lon = payload.user_longitude
    weight_kg = (
        payload.garment_weight_kg
        if (payload.garment_weight_kg and payload.garment_weight_kg > 0)
        else settings.DEFAULT_GARMENT_WEIGHT_KG
    )

    # 1. Layer A: Evaluate deterministic SQL eligibility rules in DB
    eligibility = evaluate_eligibility(db, analysis)

    # 2. Layer C: Locate nearest drop-off partner and record distances
    all_pathways = ["reuse_resell", "repair", "donate", "recycle", "brand_takeback"]
    partners = {}
    distances: Dict[str, float] = {}

    for pathway in all_pathways:
        partner = find_nearest_partner(
            db=db,
            pathway=pathway,
            user_lat=user_lat,
            user_lon=user_lon,
            brand_name=analysis.tag.brand,
        )
        partners[pathway] = partner
        # If no partner found within direct network, assign standard distant penalty (25 km)
        distances[pathway] = partner.distance_km if partner else 25.0

    # 3. Layer B: Rank pathways using Ranker interface & compute SHAP attributions
    scored_pathways, shap_scores = rank_pathways(
        analysis=analysis,
        eligibility=eligibility,
        distances=distances,
    )

    # 4. Construct RankedPathway items with cited LCA impact and partner details
    ranked_items: List[RankedPathway] = []
    for pathway, score, is_elig in scored_pathways:
        impact = calculate_impact(
            db=db,
            pathway=pathway,
            material_label=analysis.material.label,
            garment_weight_kg=weight_kg,
        )
        ranked_items.append(
            RankedPathway(
                pathway=pathway,
                score=score,
                eligible=is_elig,
                nearest_partner=partners.get(pathway),
                impact=impact,
            )
        )

    # 5. Generate template-based plain-language explanation (handles close scores & uncertainties)
    explanation = generate_explanation(ranked_items, analysis)

    # 6. Generate unique QR tracking code
    qr_id = generate_qr_id()

    # 7. Persist recommendation record into database
    top_option = ranked_items[0] if ranked_items else None
    rec_record = Recommendation(
        qr_id=qr_id,
        user_lat=user_lat,
        user_lon=user_lon,
        analysis_json=analysis.model_dump_json(),
        recommended_pathway=top_option.pathway if top_option else "recycle",
        ranked_pathways_json=json.dumps([p.model_dump() for p in ranked_items]),
        explanation=explanation,
        is_scanned=False,
    )
    db.add(rec_record)
    db.commit()

    return RecommendResponse(
        ranked_pathways=ranked_items,
        explanation=explanation,
        shap=shap_scores,
        qr_id=qr_id,
    )
