"""Orchestration and owner-scoped persistence for the fabric workflow.

SECURITY INVARIANT: every query that touches user data filters on
``owner_hash``. A record that exists but belongs to someone else is reported
as "not found", never "forbidden", so ownership is not leaked.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.fabric import decision as dec
from app.fabric import explain as explain_mod
from app.fabric import impact as impact_mod
from app.fabric import recommender
from app.fabric import schemas as sch
from app.fabric.errors import FabricError, NotFound
from app.fabric.inference import MODEL_KEYS, FabricModelRegistry, ModelRun
from app.fabric.storage import UploadStore
from app.fabric.validation import check_declared_type, validate_and_normalize
from app.models_db import CompletedProject, FabricAnalysis, SavedIdea

logger = logging.getLogger("fabric.service")

BUDGET_NOTE = (
    "Budgets are rough author estimates of extra supplies in Indian rupees, "
    "assuming you already own scissors, needle and thread. They are not measured prices."
)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _image_url(analysis_id: str) -> str:
    return f"/api/results/{analysis_id}/image"


# =============================================================== analysis
def _run_to_dict(run: ModelRun) -> Dict[str, Any]:
    p = run.prediction
    return {
        "key": run.key,
        "architecture": run.architecture,
        "available": run.available,
        "label": p.label if p else None,
        "confidence": round(p.confidence, 6) if p else None,
        "top_k": [{"label": l, "confidence": c} for l, c in (p.top_k if p else ())],
        "latency_ms": run.latency_ms,
        "reason": run.reason,
    }


def analyze_and_store(
    db: Session,
    registry: FabricModelRegistry,
    store: UploadStore,
    *,
    owner: str,
    data: bytes,
    filename: Optional[str],
    content_type: Optional[str],
    threshold: float,
    max_bytes: int,
) -> sch.AnalysisOut:
    """Validate -> infer -> decide -> persist. Raises FabricError subclasses."""
    check_declared_type(filename, content_type)
    image = validate_and_normalize(data, max_bytes=max_bytes)

    runs = registry.predict(image.to_pil())  # raises ModelsUnavailable when nothing can run
    predictions = [r.prediction for r in runs if r.available and r.prediction]
    decision = dec.decide(predictions, threshold)

    analysis_id = str(uuid.uuid4())
    stored_name = store.save(owner, image.jpeg_bytes)
    row = FabricAnalysis(
        id=analysis_id,
        owner_hash=owner,
        image_filename=stored_name,
        image_sha256=image.sha256,
        image_width=image.width,
        image_height=image.height,
        predictions_json=json.dumps(
            {"models": [_run_to_dict(r) for r in runs], "model_versions": registry.model_versions()}
        ),
        decision_json=json.dumps(_decision_to_dict(decision)),
        decision_status=decision.status,
        final_label=decision.final_label,
    )
    try:
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()
        store.delete(owner, stored_name)  # do not leave an orphan file
        raise
    db.refresh(row)
    return build_analysis_out(row, registry)


def _decision_to_dict(d: dec.Decision) -> Dict[str, Any]:
    return {
        "status": d.status,
        "final_label": d.final_label,
        "candidates": list(d.candidates),
        "low_confidence": d.low_confidence,
        "threshold": d.threshold,
        "summary": d.summary,
        "rule_id": d.rule_id,
    }


def _decision_from_dict(x: Dict[str, Any]) -> dec.Decision:
    return dec.Decision(
        status=x["status"],
        final_label=x.get("final_label"),
        candidates=tuple(x.get("candidates") or ()),
        low_confidence=bool(x.get("low_confidence")),
        threshold=float(x["threshold"]),
        summary=x["summary"],
        rule_id=x.get("rule_id", dec.RULE_ID),
    )


def build_analysis_out(row: FabricAnalysis, registry: FabricModelRegistry) -> sch.AnalysisOut:
    pred = json.loads(row.predictions_json)
    decision = _decision_from_dict(json.loads(row.decision_json))

    cat_key = recommender.normalize_category(decision.final_label)
    display = recommender.category_display(cat_key)
    explanation, steps = explain_mod.explain(decision, display)

    # Verified accuracy is only attached when the stored weights fingerprint
    # equals the currently loaded weights that the report was computed for.
    current = registry.verified_metrics()
    now_versions = registry.model_versions()
    used_versions = pred.get("model_versions") or {}
    verified: Dict[str, Optional[sch.VerifiedAccuracy]] = {}
    for key in MODEL_KEYS:
        ok = bool(used_versions.get(key)) and used_versions.get(key) == now_versions.get(key)
        summary = current.get(key) if ok else None
        verified[key] = sch.VerifiedAccuracy(**summary) if summary else None

    return sch.AnalysisOut(
        id=row.id,
        created_at=_aware(row.created_at),
        image_url=_image_url(row.id),
        image_width=row.image_width,
        image_height=row.image_height,
        models=[sch.ModelResult(**m) for m in pred["models"]],
        decision=sch.DecisionOut(
            status=decision.status,
            final_label=decision.final_label,
            final_category=display,
            candidates=list(decision.candidates),
            low_confidence=decision.low_confidence,
            threshold=decision.threshold,
            summary=decision.summary,
            rule_id=decision.rule_id,
        ),
        explanation=explanation,
        next_steps=steps,
        confidence_notice=explain_mod.CONFIDENCE_NOTICE,
        verified_accuracy=verified,
        verified_accuracy_note=None if any(verified.values()) else explain_mod.NO_VERIFIED_ACCURACY,
    )


def _get_row(db: Session, owner: str, analysis_id: str) -> FabricAnalysis:
    row = (
        db.query(FabricAnalysis)
        .filter(FabricAnalysis.id == analysis_id, FabricAnalysis.owner_hash == owner)
        .first()
    )
    if row is None:
        raise NotFound("That analysis was not found.")
    return row


def get_analysis(db: Session, registry: FabricModelRegistry, owner: str, analysis_id: str) -> sch.AnalysisOut:
    return build_analysis_out(_get_row(db, owner, analysis_id), registry)


def get_image_bytes(db: Session, store: UploadStore, owner: str, analysis_id: str) -> bytes:
    row = _get_row(db, owner, analysis_id)
    data = store.read(owner, row.image_filename)
    if data is None:
        raise NotFound("The image file for this analysis is no longer available.")
    return data


def list_analyses(db: Session, owner: str) -> sch.AnalysisList:
    rows = (
        db.query(FabricAnalysis)
        .filter(FabricAnalysis.owner_hash == owner)
        .order_by(FabricAnalysis.created_at.desc())
        .all()
    )
    saved_counts: Dict[str, int] = {}
    for s in db.query(SavedIdea).filter(SavedIdea.owner_hash == owner, SavedIdea.analysis_id.isnot(None)):
        saved_counts[s.analysis_id] = saved_counts.get(s.analysis_id, 0) + 1
    items = []
    for r in rows:
        d = json.loads(r.decision_json)
        items.append(
            sch.AnalysisSummary(
                id=r.id,
                created_at=_aware(r.created_at),
                image_url=_image_url(r.id),
                decision_status=r.decision_status,
                final_label=r.final_label,
                candidates=list(d.get("candidates") or []),
                saved_ideas_count=saved_counts.get(r.id, 0),
            )
        )
    return sch.AnalysisList(items=items)


def delete_analysis(db: Session, store: UploadStore, owner: str, analysis_id: str) -> None:
    """Delete an analysis, its saved ideas and its image file.

    Completed projects are kept (history and impact totals survive); they just
    lose the link to the deleted analysis.
    """
    row = _get_row(db, owner, analysis_id)
    filename = row.image_filename
    try:
        db.query(SavedIdea).filter(
            SavedIdea.owner_hash == owner, SavedIdea.analysis_id == analysis_id
        ).delete(synchronize_session=False)
        db.query(CompletedProject).filter(
            CompletedProject.owner_hash == owner, CompletedProject.analysis_id == analysis_id
        ).update({CompletedProject.analysis_id: None}, synchronize_session=False)
        db.delete(row)
        db.commit()
    except Exception:
        db.rollback()
        raise
    if not store.delete(owner, filename):
        logger.warning("Image file for deleted analysis %s was already missing", analysis_id)


# ======================================================== recommendations
def _idea_or_404(idea_id: str) -> Dict[str, Any]:
    idea = recommender.get_idea(idea_id)
    if idea is None:
        raise NotFound("That idea does not exist.")
    return idea


def recommendations_for(db: Session, owner: str, analysis_id: str) -> sch.RecommendationsOut:
    row = _get_row(db, owner, analysis_id)
    d = json.loads(row.decision_json)
    rs = recommender.recommend(
        d["status"], d.get("final_label"), list(d.get("candidates") or [])
    )
    saved_ids = {
        s.idea_id
        for s in db.query(SavedIdea).filter(
            SavedIdea.owner_hash == owner, SavedIdea.analysis_id == analysis_id
        )
    }
    return sch.RecommendationsOut(
        analysis_id=analysis_id,
        decision_status=d["status"],
        basis=rs.basis,
        category=rs.category,
        category_display=recommender.category_display(rs.category),
        candidate_categories=rs.candidate_categories,
        unresolved_labels=rs.unresolved_labels,
        note=rs.note,
        budget_note=BUDGET_NOTE,
        items=[
            sch.RecommendationItem(idea=sch.Idea(**i.idea), match=i.match, saved=i.idea["id"] in saved_ids)
            for i in rs.items
        ],
    )


# ============================================================ saved ideas
def _saved_out(s: SavedIdea) -> sch.SavedIdeaOut:
    return sch.SavedIdeaOut(
        id=s.id,
        idea_id=s.idea_id,
        analysis_id=s.analysis_id,
        created_at=_aware(s.created_at),
        idea=sch.Idea(**_idea_or_404(s.idea_id)),
    )


def save_idea(db: Session, owner: str, payload: sch.SavedIdeaIn) -> sch.SavedIdeaOut:
    _idea_or_404(payload.idea_id)
    if payload.analysis_id:
        _get_row(db, owner, payload.analysis_id)  # must be the caller's own analysis
    q = db.query(SavedIdea).filter(SavedIdea.owner_hash == owner, SavedIdea.idea_id == payload.idea_id)
    q = q.filter(
        SavedIdea.analysis_id.is_(None) if payload.analysis_id is None
        else SavedIdea.analysis_id == payload.analysis_id
    )
    existing = q.first()
    if existing:  # idempotent
        return _saved_out(existing)
    s = SavedIdea(owner_hash=owner, analysis_id=payload.analysis_id, idea_id=payload.idea_id)
    try:
        db.add(s)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(s)
    return _saved_out(s)


def list_saved(db: Session, owner: str) -> sch.SavedIdeaList:
    rows = (
        db.query(SavedIdea).filter(SavedIdea.owner_hash == owner).order_by(SavedIdea.created_at.desc()).all()
    )
    return sch.SavedIdeaList(items=[_saved_out(s) for s in rows if recommender.get_idea(s.idea_id)])


def delete_saved(db: Session, owner: str, saved_id: int) -> None:
    s = db.query(SavedIdea).filter(SavedIdea.id == saved_id, SavedIdea.owner_hash == owner).first()
    if s is None:
        raise NotFound("That saved idea was not found.")
    db.delete(s)
    db.commit()


# ============================================================== projects
def _project_out(p: CompletedProject) -> sch.ProjectOut:
    idea = recommender.get_idea(p.idea_id)
    return sch.ProjectOut(
        id=p.id,
        idea_id=p.idea_id,
        idea_name=idea["name"] if idea else p.idea_id,
        analysis_id=p.analysis_id,
        completed_at=_aware(p.completed_at),
        notes=p.notes,
        weight_kg=p.weight_kg,
        weight_source=p.weight_source,
    )


def add_project(db: Session, owner: str, payload: sch.ProjectIn) -> sch.ProjectOut:
    _idea_or_404(payload.idea_id)
    category: Optional[str] = None
    if payload.analysis_id:
        row = _get_row(db, owner, payload.analysis_id)
        category = recommender.normalize_category(row.final_label)
    weight, source = impact_mod.resolve_weight(category, payload.weight_kg)
    p = CompletedProject(
        owner_hash=owner,
        analysis_id=payload.analysis_id,
        idea_id=payload.idea_id,
        notes=(payload.notes or "").strip() or None,
        weight_kg=weight,
        weight_source=source,
    )
    try:
        db.add(p)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(p)
    return _project_out(p)


def list_projects(db: Session, owner: str) -> sch.ProjectList:
    rows = (
        db.query(CompletedProject)
        .filter(CompletedProject.owner_hash == owner)
        .order_by(CompletedProject.completed_at.desc())
        .all()
    )
    return sch.ProjectList(items=[_project_out(p) for p in rows])


def delete_project(db: Session, owner: str, project_id: int) -> None:
    p = db.query(CompletedProject).filter(
        CompletedProject.id == project_id, CompletedProject.owner_hash == owner
    ).first()
    if p is None:
        raise NotFound("That project was not found.")
    db.delete(p)
    db.commit()


# =============================================================== impact
def impact_for(db: Session, owner: str) -> sch.ImpactOut:
    analyses = db.query(FabricAnalysis).filter(FabricAnalysis.owner_hash == owner).count()
    saved = db.query(SavedIdea).filter(SavedIdea.owner_hash == owner).count()
    projects = (
        db.query(CompletedProject)
        .filter(CompletedProject.owner_hash == owner)
        .order_by(CompletedProject.completed_at.desc())
        .all()
    )
    summary = impact_mod.summarize(
        analyses_count=analyses,
        saved_ideas_count=saved,
        projects=[{"weight_kg": p.weight_kg, "weight_source": p.weight_source} for p in projects],
    )
    return sch.ImpactOut(**summary, recent_projects=[_project_out(p) for p in projects[:10]])