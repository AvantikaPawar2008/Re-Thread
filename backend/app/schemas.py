"""Pydantic API Schemas for RE-THREAD.

Single Source of Truth defining the fixed API contract specified in
docs/PROJECT.md Section 11.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums / Literal Types
# ---------------------------------------------------------------------------
MaterialLabel = Literal["natural", "synthetic", "blend", "uncertain"]
ConditionLabel = Literal["new", "gently_used", "worn", "heavily_worn"]
CompositionStatus = Literal["confident", "uncertain"]
PathwayType = Literal["reuse_resell", "repair", "donate", "recycle", "brand_takeback"]


# ---------------------------------------------------------------------------
# Stage 2: Analyze Garment Schemas (POST /analyze)
# ---------------------------------------------------------------------------
class MaterialAnalysis(BaseModel):
    label: MaterialLabel = Field(
        ...,
        description="Coarse material class: natural, synthetic, blend, or uncertain.",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model prediction confidence score."
    )
    heatmap_base64: Optional[str] = Field(
        default=None,
        description="Grad-CAM visual attention heatmap overlay encoded as base64 data URI.",
    )


class ConditionAnalysis(BaseModel):
    label: ConditionLabel = Field(
        ...,
        description="Garment condition: new, gently_used, worn, or heavily_worn.",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model prediction confidence score."
    )
    heatmap_base64: Optional[str] = Field(
        default=None,
        description="Grad-CAM visual attention heatmap overlay encoded as base64 data URI.",
    )


class DamageBox(BaseModel):
    x1: float = Field(..., description="Normalized or pixel bounding box min x")
    y1: float = Field(..., description="Normalized or pixel bounding box min y")
    x2: float = Field(..., description="Normalized or pixel bounding box max x")
    y2: float = Field(..., description="Normalized or pixel bounding box max y")
    label: Optional[str] = Field(default="damage", description="Damage category e.g. tear, stain, hole")
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)


class DamageAnalysis(BaseModel):
    detected: bool = Field(..., description="Whether visible damage was detected.")
    area_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of garment area damaged."
    )
    boxes: List[DamageBox] = Field(
        default_factory=list, description="List of detected damage bounding boxes."
    )


class TagAnalysis(BaseModel):
    brand: Optional[str] = Field(
        default=None,
        description="Extracted & fuzzy-matched brand name, or None if unreadable.",
    )
    composition: Dict[str, float] = Field(
        default_factory=dict,
        description="Fiber breakdown percentages e.g. {'cotton': 60.0, 'polyester': 40.0}.",
    )
    ocr_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Average OCR confidence."
    )
    agrees_with_vision: bool = Field(
        default=True,
        description="True if parsed composition matches coarse vision prediction.",
    )


class AnalyzeResponse(BaseModel):
    """The exact response shape for POST /analyze (Section 11)."""
    material: MaterialAnalysis
    condition: ConditionAnalysis
    damage: DamageAnalysis
    tag: TagAnalysis
    composition_status: CompositionStatus


# ---------------------------------------------------------------------------
# Stage 3 & 4: Recommend Pathways Schemas (POST /recommend)
# ---------------------------------------------------------------------------
class PartnerDropoff(BaseModel):
    name: str = Field(..., description="Drop-off partner name.")
    distance_km: float = Field(
        ..., ge=0.0, description="Distance from user in kilometers."
    )
    address: Optional[str] = Field(default=None, description="Partner facility street address.")
    contact_phone: Optional[str] = Field(default=None)


class ImpactEstimate(BaseModel):
    water_litres_saved: float = Field(
        ..., ge=0.0, description="Estimated water savings in litres from lifecycle benchmark."
    )
    co2_kg_saved: float = Field(
        ..., ge=0.0, description="Estimated CO2 avoided in kg from lifecycle benchmark."
    )


class RankedPathway(BaseModel):
    pathway: str = Field(..., description="Pathway name: reuse_resell, repair, donate, recycle, brand_takeback.")
    score: float = Field(..., ge=0.0, le=1.0, description="Ranking suitability score.")
    eligible: bool = Field(..., description="True if garment meets rule constraints.")
    nearest_partner: Optional[PartnerDropoff] = Field(
        default=None, description="Closest eligible drop-off facility."
    )
    impact: ImpactEstimate


class RecommendRequest(BaseModel):
    analysis: AnalyzeResponse = Field(
        ..., description="Output from the /analyze step."
    )
    user_latitude: float = Field(
        ..., ge=-90.0, le=90.0, description="User's current latitude for distance ranking."
    )
    user_longitude: float = Field(
        ..., ge=-180.0, le=180.0, description="User's current longitude for distance ranking."
    )
    garment_weight_kg: Optional[float] = Field(
        default=0.3,
        gt=0.0,
        description="Estimated garment weight in kg for impact calculations (default 0.3kg).",
    )


class RecommendResponse(BaseModel):
    """The exact response shape for POST /recommend (Section 11)."""
    ranked_pathways: List[RankedPathway]
    explanation: str = Field(
        ..., description="Plain-language decision explanation for user."
    )
    shap: Dict[str, float] = Field(
        default_factory=dict,
        description="Feature attribution values (e.g. material, condition, damage_percent, brand).",
    )
    qr_id: str = Field(
        ..., description="Unique lifecycle QR tracking ID for this recommendation."
    )


# ---------------------------------------------------------------------------
# Stage 5: Lifecycle Outcome Schemas (POST /outcome/confirm)
# ---------------------------------------------------------------------------
class OutcomeConfirmRequest(BaseModel):
    qr_id: str = Field(..., description="QR identifier scanned at partner facility.")
    partner_facility_id: int = Field(..., description="ID of scanning partner facility.")
    confirmed_pathway: str = Field(..., description="Actual accepted pathway.")
    notes: Optional[str] = Field(default=None, description="Optional drop-off intake notes.")


class OutcomeConfirmResponse(BaseModel):
    status: str = "confirmed"
    qr_id: str
    message: str


# ---------------------------------------------------------------------------
# System / Health Schemas
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "RE-THREAD"
    version: str = "0.1.0"
    database: str = "connected"
