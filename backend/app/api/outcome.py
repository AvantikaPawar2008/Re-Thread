"""Endpoint: POST /outcome/confirm

Scanned by partner drop-off locations to confirm real intake outcomes
(Non-Negotiable Rule #7: Only QR-confirmed outcomes count as real data).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models_db import Outcome, Recommendation
from backend.app.schemas import OutcomeConfirmRequest, OutcomeConfirmResponse

router = APIRouter()


@router.post(
    "/outcome/confirm",
    response_model=OutcomeConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm drop-off intake by scanning QR code",
    description="Drop-off partners scan the garment's QR code upon receiving the item to record ground truth.",
)
def confirm_outcome(
    payload: OutcomeConfirmRequest,
    db: Session = Depends(get_db),
) -> OutcomeConfirmResponse:
    # 1. Lookup recommendation by QR identifier
    rec = db.query(Recommendation).filter(Recommendation.qr_id == payload.qr_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with QR code '{payload.qr_id}' not found.",
        )

    # 2. Mark recommendation as scanned
    rec.is_scanned = True

    # 3. Create verified outcome entry
    outcome = Outcome(
        qr_id=payload.qr_id,
        recommendation_id=rec.id,
        partner_facility_id=payload.partner_facility_id,
        confirmed_pathway=payload.confirmed_pathway,
        partner_notes=payload.notes,
    )
    db.add(outcome)
    db.commit()

    return OutcomeConfirmResponse(
        status="confirmed",
        qr_id=payload.qr_id,
        message=f"Garment intake successfully confirmed for pathway '{payload.confirmed_pathway}'.",
    )
