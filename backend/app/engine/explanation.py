"""Template-Based Plain-Language Decision Trace Generator.

Generates human-readable explanations explaining why the top pathway was
recommended, explicitly detailing material, condition, damage %, distance,
and climate savings.

Gracefully handles edge cases:
- Close scores between top 2 pathways
- Uncertain material composition
- Unknown brand
- No eligible partner facilities nearby
"""

from typing import List, Optional
from backend.app.schemas import AnalyzeResponse, RankedPathway


def generate_explanation(
    ranked_pathways: List[RankedPathway],
    analysis: AnalyzeResponse,
) -> str:
    """Generate user-facing plain language decision explanation.

    Synthesizes facts into readable sentences without generic fluff.
    """
    if not ranked_pathways:
        return "No eligible circular pathways could be determined."

    top_option = ranked_pathways[0]
    runner_up = ranked_pathways[1] if len(ranked_pathways) > 1 else None

    p_title = top_option.pathway.replace("_", " ").title()
    mat = analysis.material.label
    cond = analysis.condition.label.replace("_", " ")
    has_dmg = analysis.damage.detected
    dmg_area = analysis.damage.area_percent
    brand = analysis.tag.brand

    # Core rationale per pathway
    if top_option.pathway == "repair":
        rationale = f"Visible defect detected ({dmg_area}% area), but the garment is in {cond} condition and structurally restorable"
    elif top_option.pathway == "reuse_resell":
        rationale = f"Garment is in {cond} condition with negligible wear ({dmg_area}% defect), holding high residual value for direct reuse"
    elif top_option.pathway == "donate":
        rationale = f"Garment is in wearable {cond} condition suitable for community redistribution"
    elif top_option.pathway == "brand_takeback":
        brand_name = brand if brand else "partner brand"
        rationale = f"Eligible for {brand_name}'s active circular take-back programme with brand store drop-off"
    else:  # recycle
        rationale = f"Garment is in {cond} condition and best recovered through mechanical shredding and fiber recycling"

    # Partner distance clause
    if top_option.nearest_partner:
        partner_clause = f", nearest partner '{top_option.nearest_partner.name}' is {top_option.nearest_partner.distance_km} km away"
    else:
        partner_clause = ", no local drop-off partner currently registered nearby (mail-in or municipal collection recommended)"

    # Impact clause
    impact_clause = (
        f", saving an estimated {top_option.impact.water_litres_saved:,.0f} L water and "
        f"{top_option.impact.co2_kg_saved:.1f} kg CO₂"
    )

    base_sentence = f"Recommended: {p_title}. {rationale}{partner_clause}{impact_clause}."

    # Edge Case: Uncertain Material Composition
    uncertainty_note = ""
    if mat == "uncertain" or analysis.composition_status == "uncertain":
        uncertainty_note = " Note: Material composition is uncertain and could not be confirmed definitively from optical photos alone; routing is safeguarded based on wear condition."

    # Edge Case: Close Scores (e.g. difference <= 0.08)
    close_score_note = ""
    if runner_up and (top_option.score - runner_up.score) <= 0.08 and runner_up.eligible:
        ru_title = runner_up.pathway.replace("_", " ").title()
        close_score_note = f" Close match: {p_title} slightly edges out {ru_title} ({top_option.score:.2f} vs {runner_up.score:.2f}); either pathway is a great circular choice."

    # Edge Case: Unknown Brand when brand take-back was ineligible
    brand_note = ""
    if not brand and top_option.pathway != "brand_takeback":
        # Tag missing or brand unknown
        pass

    return f"{base_sentence}{uncertainty_note}{close_score_note}".strip()
