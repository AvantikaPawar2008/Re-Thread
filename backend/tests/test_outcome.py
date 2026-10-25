"""Tests for POST /outcome/confirm (Lifecycle QR Loop)."""


def test_outcome_confirmation_flow(client):
    """Test generating a recommendation QR code and confirming it via partner scan."""
    # 1. Generate recommendation
    rec_payload = {
        "analysis": {
            "material": {"label": "natural", "confidence": 0.85},
            "condition": {"label": "worn", "confidence": 0.70},
            "damage": {"detected": False, "area_percent": 0.0, "boxes": []},
            "tag": {
                "brand": "Zara",
                "composition": {"cotton": 100.0},
                "ocr_confidence": 0.90,
                "agrees_with_vision": True,
            },
            "composition_status": "confident",
        },
        "user_latitude": 18.5204,
        "user_longitude": 73.8567,
    }
    rec_resp = client.post("/recommend", json=rec_payload)
    assert rec_resp.status_code == 200
    qr_id = rec_resp.json()["qr_id"]

    # 2. Partner scans QR code to confirm outcome
    confirm_payload = {
        "qr_id": qr_id,
        "partner_facility_id": 1,
        "confirmed_pathway": "donate",
        "notes": "Received clean cotton shirt in good condition.",
    }
    confirm_resp = client.post("/outcome/confirm", json=confirm_payload)
    assert confirm_resp.status_code == 200
    data = confirm_resp.json()
    assert data["status"] == "confirmed"
    assert data["qr_id"] == qr_id


def test_outcome_confirm_nonexistent_qr_fails(client):
    """Scanning an unrecorded QR code should return 404."""
    payload = {
        "qr_id": "rt-nonexistent-qr",
        "partner_facility_id": 1,
        "confirmed_pathway": "recycle",
    }
    response = client.post("/outcome/confirm", json=payload)
    assert response.status_code == 404
