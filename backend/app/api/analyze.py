"""Endpoint: POST /analyze

Accepts multipart/form-data garment images and an optional care tag image.

Perception priority order:
  1. Local trained weights (if all three .pt files are present)
  2. VLM API        (if VLM_API_KEY is set in .env)
  3. Typed stub     (silent fallback, never crashes /analyze)

Requirement #6: Grad-CAM is disabled (null) when source is "vlm".
"""

from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status

try:
    from app.ml.condition import analyze_condition, is_using_stub as condition_stub
    from app.ml.damage import analyze_damage, is_using_stub as damage_stub
    from app.ml.material import analyze_material, is_using_stub as material_stub
    from app.ml.tag.clean import clean_tag_image
    from app.ml.tag.detect import detect_tag
    from app.ml.tag.ocr import extract_tag_text
    from app.ml.tag.parse import parse_tag_and_crosscheck
    from app.ml.vlm import vlm_analyze, vlm_available
    from app.schemas import AnalyzeResponse
except ImportError:
    from backend.app.ml.condition import analyze_condition, is_using_stub as condition_stub
    from backend.app.ml.damage import analyze_damage, is_using_stub as damage_stub
    from backend.app.ml.material import analyze_material, is_using_stub as material_stub
    from backend.app.ml.tag.clean import clean_tag_image
    from backend.app.ml.tag.detect import detect_tag
    from backend.app.ml.tag.ocr import extract_tag_text
    from backend.app.ml.tag.parse import parse_tag_and_crosscheck
    from backend.app.ml.vlm import vlm_analyze, vlm_available
    from backend.app.schemas import AnalyzeResponse

router = APIRouter()


def _local_models_ready() -> bool:
    """Return True only if ALL local perception models are loaded (not stub)."""
    return not (condition_stub() or damage_stub() or material_stub())


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze garment images and optional care label",
    description=(
        "Uploads garment photos and optional care tag photo to predict material, "
        "condition, damage, and parsed tag details. "
        "Uses local models if present, VLM API if configured, otherwise typed stub."
    ),
)
async def analyze_garment(
    garment_images: List[UploadFile] = File(
        ...,
        description="One or more photos of the garment (full view, fabric texture, damage detail).",
    ),
    tag_image: Optional[UploadFile] = File(
        None,
        description="Optional close-up photograph of the garment's care label.",
    ),
) -> AnalyzeResponse:
    if not garment_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one garment photo is required.",
        )

    # Read garment image bytes
    garment_bytes_list: List[bytes] = []
    for img in garment_images:
        content = await img.read()
        if content:
            garment_bytes_list.append(content)

    if not garment_bytes_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded garment images are empty.",
        )

    # Read tag image bytes (optional)
    tag_bytes: Optional[bytes] = None
    if tag_image is not None and tag_image.filename:
        raw = await tag_image.read()
        if raw:
            tag_bytes = raw

    # ── Priority 1: Local trained models ─────────────────────────────────────
    if _local_models_ready():
        return await _run_local_pipeline(garment_bytes_list, tag_bytes)

    # ── Priority 2: VLM API ───────────────────────────────────────────────────
    if vlm_available():
        return await _run_vlm_pipeline(garment_bytes_list, tag_bytes)

    # ── Priority 3: Stub ──────────────────────────────────────────────────────
    return await _run_local_pipeline(garment_bytes_list, tag_bytes)


async def _run_local_pipeline(
    garment_bytes_list: List[bytes],
    tag_bytes: Optional[bytes],
) -> AnalyzeResponse:
    """Run the local model (or stub) perception pipeline."""
    material_res = analyze_material(garment_bytes_list)
    condition_res = analyze_condition(garment_bytes_list)
    damage_res = analyze_damage(garment_bytes_list)

    source = "local" if _local_models_ready() else "stub"

    tag_ocr_lines = []
    if tag_bytes is not None:
        crop_coords = detect_tag(tag_bytes)
        cleaned = clean_tag_image(tag_bytes)
        tag_ocr_lines = extract_tag_text(cleaned)

    tag_res, composition_status = parse_tag_and_crosscheck(
        ocr_lines=tag_ocr_lines,
        vision_material=material_res.label,
    )

    return AnalyzeResponse(
        material=material_res,
        condition=condition_res,
        damage=damage_res,
        tag=tag_res,
        composition_status=composition_status,
        source=source,
        reasoning=None,
    )


async def _run_vlm_pipeline(
    garment_bytes_list: List[bytes],
    tag_bytes: Optional[bytes],
) -> AnalyzeResponse:
    """Run the VLM perception pipeline. Never raises — falls back to stub on error."""
    try:
        response, source, reasoning = await vlm_analyze(garment_bytes_list, tag_bytes)

        if (
            tag_bytes is not None
            and not response.tag.composition
            and response.tag.ocr_confidence == 0.0
        ):
            try:
                crop_coords = detect_tag(tag_bytes)
                cleaned = clean_tag_image(tag_bytes)
                tag_ocr_lines = extract_tag_text(cleaned)
                if tag_ocr_lines:
                    tag_res, composition_status = parse_tag_and_crosscheck(
                        ocr_lines=tag_ocr_lines,
                        vision_material=response.material.label,
                    )
                    response = response.model_copy(update={
                        "tag": tag_res,
                        "composition_status": composition_status,
                    })
            except Exception:
                pass

        response = response.model_copy(update={"source": source, "reasoning": reasoning})
        return response

    except Exception as e:
        import logging
        logging.getLogger("ml.vlm").error(f"VLM pipeline unexpected error: {e}")
        try:
            from app.ml.vlm import _stub_response
        except ImportError:
            from backend.app.ml.vlm import _stub_response
        stub = _stub_response()
        stub = stub.model_copy(update={"source": "stub", "reasoning": None})
        return stub
