"""Pydantic response/request models for the /api/* fabric endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorBody


# ----------------------------------------------------------------- analysis
class TopK(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ModelResult(BaseModel):
    key: Literal["resnet50", "nasnet"]
    architecture: str
    available: bool
    label: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_k: List[TopK] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    reason: Optional[str] = Field(default=None, description="Why the model produced no output.")


class DecisionOut(BaseModel):
    status: Literal["agreement", "weak_agreement", "disagreement", "single_model", "uncertain"]
    final_label: Optional[str] = None
    final_category: Optional[str] = Field(default=None, description="Display name of the matching recipe-catalog category, if any.")
    candidates: List[str]
    low_confidence: bool
    threshold: float
    summary: str
    rule_id: str


class VerifiedAccuracy(BaseModel):
    accuracy: float
    macro_f1: float
    n_test_images: int
    evaluated_at: str
    note: str


class AnalysisOut(BaseModel):
    id: str
    created_at: datetime
    image_url: str = Field(..., description="Authenticated endpoint that returns the stored image.")
    image_width: int
    image_height: int
    models: List[ModelResult]
    decision: DecisionOut
    explanation: str
    next_steps: List[str]
    confidence_notice: str
    verified_accuracy: Dict[str, Optional[VerifiedAccuracy]] = Field(
        ..., description="Per-model accuracy measured on held-out test images; null when no verified report exists for these exact weights."
    )
    verified_accuracy_note: Optional[str] = None


class AnalysisSummary(BaseModel):
    id: str
    created_at: datetime
    image_url: str
    decision_status: str
    final_label: Optional[str]
    candidates: List[str]
    saved_ideas_count: int = 0


class AnalysisList(BaseModel):
    items: List[AnalysisSummary]


# ------------------------------------------------------------------- ideas
class Idea(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    tagline: str
    difficulty: Literal["Easy", "Medium", "Advanced"]
    time_minutes: List[int]
    sewing: Literal["none", "hand", "machine"]
    budget_inr: List[int]
    applies_to: List[str]
    materials: List[str]
    optional_materials: List[str] = Field(default_factory=list)
    steps: List[str]
    caveat: Optional[str] = None
    image: str


class IdeaList(BaseModel):
    items: List[Idea]
    budget_note: str


class RecommendationItem(BaseModel):
    idea: Idea
    match: Literal["category", "shared", "universal"]
    saved: bool = False


class RecommendationsOut(BaseModel):
    analysis_id: str
    decision_status: str
    basis: Literal["category", "shared", "universal"]
    category: Optional[str] = None
    category_display: Optional[str] = None
    candidate_categories: List[str]
    unresolved_labels: List[str]
    note: str
    budget_note: str
    items: List[RecommendationItem]


# ----------------------------------------------------------- saved / projects
class SavedIdeaIn(BaseModel):
    idea_id: str = Field(..., min_length=1, max_length=64)
    analysis_id: Optional[str] = Field(default=None, max_length=36)


class SavedIdeaOut(BaseModel):
    id: int
    idea_id: str
    analysis_id: Optional[str]
    created_at: datetime
    idea: Idea


class SavedIdeaList(BaseModel):
    items: List[SavedIdeaOut]


class ProjectIn(BaseModel):
    idea_id: str = Field(..., min_length=1, max_length=64)
    analysis_id: Optional[str] = Field(default=None, max_length=36)
    notes: Optional[str] = Field(default=None, max_length=500)
    weight_kg: Optional[float] = Field(
        default=None, gt=0, le=20, description="Optional: the garment's actual weight, if you weighed it."
    )


class ProjectOut(BaseModel):
    id: int
    idea_id: str
    idea_name: str
    analysis_id: Optional[str]
    completed_at: datetime
    notes: Optional[str]
    weight_kg: float
    weight_source: Literal["user", "assumed_category", "assumed_default"]


class ProjectList(BaseModel):
    items: List[ProjectOut]


# ------------------------------------------------------------------ impact
class ImpactOut(BaseModel):
    analyses_count: int
    saved_ideas_count: int
    completed_projects_count: int
    garments_reused_estimate: int
    fabric_kg_diverted_upper_bound: float
    fabric_kg_from_user_weights: float
    fabric_kg_from_assumed_weights: float
    environmental: Dict[str, Any]
    assumptions: List[str]
    is_estimate: bool
    recent_projects: List[ProjectOut]


# ------------------------------------------------------------------ models
class ModelStatusOut(BaseModel):
    key: str
    architecture: Optional[str]
    state: Literal["loaded", "missing", "error"]
    reason: Optional[str]
    num_classes: Optional[int]
    class_names: List[str]
    verified_accuracy: Optional[VerifiedAccuracy] = None


class ModelsStatusOut(BaseModel):
    models: List[ModelStatusOut]
    any_available: bool
    both_available: bool
    class_names: List[str]
    agreement: Optional[Dict[str, Any]] = None
    notice: str