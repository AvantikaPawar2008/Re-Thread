"""Endpoint: POST /analyze

Accepts multipart/form-data garment images and an optional care tag image.
Orchestrates vision models (material, condition, damage) and tag OCR cross-checking.
"""

from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.ml.condition import analyze_condition
from backend.app.ml.damage import analyze_damage
from backend.app.ml.material import analyze_material
from backend.app.ml.tag.clean import clean_tag_image
from backend.app.ml.tag.detect import detect_tag
from backend.app.ml.tag.ocr import extract_tag_text
from backend.app.ml.tag.parse import parse_tag_and_crosscheck
from backend.app.schemas import AnalyzeResponse

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze garment images and optional care label",
    description="Uploads garment photos and optional care tag photo to predict material, condition, damage, and parsed tag details.",
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

    # 1. Vision models (Stage 2)
    material_res = analyze_material(garment_bytes_list)
    condition_res = analyze_condition(garment_bytes_list)
    damage_res = analyze_damage(garment_bytes_list)

    # 2. Care tag pipeline (Stage 1) - optional / graceful degradation (Rule #6)
    tag_ocr_lines = []
    if tag_image is not None and tag_image.filename:
        tag_bytes = await tag_image.read()
        if tag_bytes:
            # Crop, clean, OCR
            crop_coords = detect_tag(tag_bytes)
            cleaned = clean_tag_image(tag_bytes)
            tag_ocr_lines = extract_tag_text(cleaned)

    # 3. Parse tag and cross-check against vision material prediction
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
    )
