"""Fabric upcycling API (``/api/*``).

Endpoints
---------
GET    /api/models                       model availability + verified metrics
POST   /api/analyze                      upload an image and run ResNet50 + NASNet
GET    /api/results                      list the caller's analyses
GET    /api/results/{id}                 one analysis
GET    /api/results/{id}/image           the stored image (owner only)
DELETE /api/results/{id}                 delete analysis + saved ideas + image file
GET    /api/recommendations/{id}         craft ideas for an analysis
GET    /api/ideas, /api/ideas/{idea_id}  browse the catalog (public, no user data)
GET/POST/DELETE /api/saved               bookmarked ideas
GET/POST/DELETE /api/projects            completed reuse projects
GET    /api/impact                       aggregate impact estimate

All endpoints except /api/models and /api/ideas* require the ``X-Guest-Id``
header and only ever return the caller's own records.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.fabric import recommender
from app.fabric import schemas as sch
from app.fabric import service
from app.fabric.auth import InvalidGuestToken, owner_hash
from app.fabric.errors import FabricError, NotFound
from app.fabric.explain import CONFIDENCE_NOTICE
from app.fabric.inference import MODEL_KEYS, FabricModelRegistry
from app.fabric.runtime import get_registry, get_store
from app.fabric.storage import UploadStore
from app.fabric.validation import ImageValidationError

logger = logging.getLogger("rethread.api.fabric")

router = APIRouter(prefix="/api")

_ERRORS = {
    400: {"model": sch.ErrorResponse}, 404: {"model": sch.ErrorResponse},
    413: {"model": sch.ErrorResponse}, 415: {"model": sch.ErrorResponse},
    503: {"model": sch.ErrorResponse},
}


def current_owner(x_guest_id: Optional[str] = Header(default=None, alias="X-Guest-Id")) -> str:
    try:
        return owner_hash(settings.APP_SECRET_KEY, x_guest_id or "")
    except InvalidGuestToken:
        raise FabricError(
            "Your session could not be identified. Reload the page and try again.",
            code="invalid_guest_id",
            http_status=401,
        )


async def _read_capped(upload: UploadFile, limit: int) -> bytes:
    """Read at most ``limit`` bytes; never buffer an oversized body."""
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise ImageValidationError(
            "file_too_large",
            f"The image is too large. The maximum size is {limit // (1024 * 1024)} MB.",
            413,
        )
    return data


# --------------------------------------------------------------- models
@router.get("/models", response_model=sch.ModelsStatusOut, tags=["Fabric AI"], summary="Model availability")
def models_status(registry: FabricModelRegistry = Depends(get_registry)) -> sch.ModelsStatusOut:
    st = registry.status()
    verified = registry.verified_metrics()
    out = []
    for key in MODEL_KEYS:
        s = st[key]
        v = verified.get(key)
        out.append(
            sch.ModelStatusOut(
                key=key,
                architecture=s.architecture,
                state=s.state,
                reason=s.reason,
                num_classes=s.num_classes,
                class_names=s.class_names,
                verified_accuracy=sch.VerifiedAccuracy(**v) if v else None,
            )
        )
    both = all(st[k].available for k in MODEL_KEYS)
    any_ = any(st[k].available for k in MODEL_KEYS)
    notice = CONFIDENCE_NOTICE
    if not any_:
        notice = (
            "No trained models are installed, so image analysis is unavailable. "
            "See the README for how to train the ResNet50 and NASNet classifiers."
        )
    return sch.ModelsStatusOut(
        models=out,
        any_available=any_,
        both_available=both,
        class_names=registry.class_names(),
        agreement=verified.get("agreement"),
        notice=notice,
    )


# -------------------------------------------------------------- analysis
@router.post(
    "/analyze",
    response_model=sch.AnalysisOut,
    responses=_ERRORS,
    tags=["Fabric AI"],
    summary="Upload a garment/fabric photo and analyse it",
)
async def analyze(
    file: UploadFile = File(..., description="JPG, JPEG, PNG or WEBP image."),
    owner: str = Depends(current_owner),
    db: Session = Depends(get_db),
    registry: FabricModelRegistry = Depends(get_registry),
    store: UploadStore = Depends(get_store),
) -> sch.AnalysisOut:
    data = await _read_capped(file, settings.max_upload_bytes)
    return service.analyze_and_store(
        db, registry, store,
        owner=owner,
        data=data,
        filename=file.filename,
        content_type=file.content_type,
        threshold=settings.CONFIDENCE_THRESHOLD,
        max_bytes=settings.max_upload_bytes,
    )


@router.get("/results", response_model=sch.AnalysisList, tags=["Fabric AI"], summary="List my analyses")
def results_list(owner: str = Depends(current_owner), db: Session = Depends(get_db)) -> sch.AnalysisList:
    return service.list_analyses(db, owner)


@router.get("/results/{analysis_id}", response_model=sch.AnalysisOut, responses=_ERRORS, tags=["Fabric AI"])
def result_get(
    analysis_id: str,
    owner: str = Depends(current_owner),
    db: Session = Depends(get_db),
    registry: FabricModelRegistry = Depends(get_registry),
) -> sch.AnalysisOut:
    return service.get_analysis(db, registry, owner, analysis_id)


@router.get("/results/{analysis_id}/image", responses={**_ERRORS, 200: {"content": {"image/jpeg": {}}}}, tags=["Fabric AI"])
def result_image(
    analysis_id: str,
    owner: str = Depends(current_owner),
    db: Session = Depends(get_db),
    store: UploadStore = Depends(get_store),
) -> Response:
    data = service.get_image_bytes(db, store, owner, analysis_id)
    return Response(
        content=data,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/results/{analysis_id}", status_code=204, responses=_ERRORS, tags=["Fabric AI"])
def result_delete(
    analysis_id: str,
    owner: str = Depends(current_owner),
    db: Session = Depends(get_db),
    store: UploadStore = Depends(get_store),
) -> Response:
    service.delete_analysis(db, store, owner, analysis_id)
    return Response(status_code=204)


# ------------------------------------------------------- recommendations
@router.get(
    "/recommendations/{analysis_id}",
    response_model=sch.RecommendationsOut,
    responses=_ERRORS,
    tags=["Craft Ideas"],
    summary="Craft ideas matched to an analysis",
)
def recommendations(
    analysis_id: str, owner: str = Depends(current_owner), db: Session = Depends(get_db)
) -> sch.RecommendationsOut:
    return service.recommendations_for(db, owner, analysis_id)


@router.get("/ideas", response_model=sch.IdeaList, tags=["Craft Ideas"], summary="Browse the whole idea catalog")
def ideas_list(
    difficulty: Optional[str] = Query(default=None, pattern="^(?i:easy|medium|advanced)$"),
    category: Optional[str] = Query(default=None, max_length=40),
    q: Optional[str] = Query(default=None, max_length=80),
) -> sch.IdeaList:
    items = recommender.list_ideas(difficulty=difficulty, category=category, query=q)
    return sch.IdeaList(items=[sch.Idea(**i) for i in items], budget_note=service.BUDGET_NOTE)


@router.get("/ideas/{idea_id}", response_model=sch.Idea, responses=_ERRORS, tags=["Craft Ideas"])
def idea_get(idea_id: str) -> sch.Idea:
    idea = recommender.get_idea(idea_id)
    if idea is None:
        raise NotFound("That idea does not exist.")
    return sch.Idea(**idea)


# ------------------------------------------------------------ saved ideas
@router.get("/saved", response_model=sch.SavedIdeaList, tags=["Saved & Projects"])
def saved_list(owner: str = Depends(current_owner), db: Session = Depends(get_db)) -> sch.SavedIdeaList:
    return service.list_saved(db, owner)


@router.post("/saved", response_model=sch.SavedIdeaOut, status_code=201, responses=_ERRORS, tags=["Saved & Projects"])
def saved_add(
    payload: sch.SavedIdeaIn, owner: str = Depends(current_owner), db: Session = Depends(get_db)
) -> sch.SavedIdeaOut:
    return service.save_idea(db, owner, payload)


@router.delete("/saved/{saved_id}", status_code=204, responses=_ERRORS, tags=["Saved & Projects"])
def saved_delete(saved_id: int, owner: str = Depends(current_owner), db: Session = Depends(get_db)) -> Response:
    service.delete_saved(db, owner, saved_id)
    return Response(status_code=204)


# --------------------------------------------------------------- projects
@router.get("/projects", response_model=sch.ProjectList, tags=["Saved & Projects"])
def projects_list(owner: str = Depends(current_owner), db: Session = Depends(get_db)) -> sch.ProjectList:
    return service.list_projects(db, owner)


@router.post("/projects", response_model=sch.ProjectOut, status_code=201, responses=_ERRORS, tags=["Saved & Projects"])
def projects_add(
    payload: sch.ProjectIn, owner: str = Depends(current_owner), db: Session = Depends(get_db)
) -> sch.ProjectOut:
    return service.add_project(db, owner, payload)


@router.delete("/projects/{project_id}", status_code=204, responses=_ERRORS, tags=["Saved & Projects"])
def projects_delete(project_id: int, owner: str = Depends(current_owner), db: Session = Depends(get_db)) -> Response:
    service.delete_project(db, owner, project_id)
    return Response(status_code=204)


# ----------------------------------------------------------------- impact
@router.get("/impact", response_model=sch.ImpactOut, tags=["Impact"], summary="My estimated impact")
def impact(owner: str = Depends(current_owner), db: Session = Depends(get_db)) -> sch.ImpactOut:
    return service.impact_for(db, owner)