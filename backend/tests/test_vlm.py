"""Tests for VLM client: valid JSON, invalid JSON, timeout, missing key.

All tests mock the VLM provider — no real API calls are made.
Run with:  python -m pytest backend/tests/test_vlm.py -v
"""

import io
import json
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

try:
    from app.ml.vlm import (
        _VLMResponse,
        _apply_rules,
        _extract_json,
        _stub_response,
        vlm_analyze,
    )
except ImportError:
    from backend.app.ml.vlm import (
        _VLMResponse,
        _apply_rules,
        _extract_json,
        _stub_response,
        vlm_analyze,
    )

# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_VLM_JSON = {
    "material_label": "natural",
    "material_confidence": 0.88,
    "condition_label": "gently_used",
    "condition_confidence": 0.75,
    "damage": {
        "detected": True,
        "area_percent": 4.2,
        "boxes": [{"x1": 0.1, "y1": 0.2, "x2": 0.3, "y2": 0.4}],
        "type": "tear",
    },
    "tag": {
        "brand": "Levi's",
        "composition": {"cotton": 80.0, "polyester": 20.0},
        "ocr_confidence": 0.91,
        "readable": True,
    },
    "reasoning": {
        "material": "The fabric shows natural cotton weave texture under close inspection.",
        "condition": "Minor surface fading visible but seams intact, consistent with gentle use.",
        "damage": "Small tear on left side approximately 4% of garment area.",
        "tag": "Care label clearly shows 80% cotton / 20% polyester printed text.",
    },
}

# Create a valid 10x10 JPEG for PIL operations
_img = Image.new("RGB", (10, 10), color="blue")
_buf = io.BytesIO()
_img.save(_buf, format="JPEG")
TINY_IMAGE = _buf.getvalue()


# ── 1. Valid JSON response ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_valid_json_response():
    """VLM returns valid JSON → AnalyzeResponse with source='vlm'."""
    with patch("backend.app.ml.vlm._provider") as mock_provider:
        mock_provider.call = AsyncMock(return_value=json.dumps(VALID_VLM_JSON))

        response, source, reasoning = await vlm_analyze([TINY_IMAGE])

        assert source == "vlm"
        assert response.material.label == "natural"
        assert response.material.confidence == pytest.approx(0.88, abs=0.01)
        assert response.condition.label == "gently_used"
        assert response.damage.detected is True
        assert response.damage.area_percent == pytest.approx(4.2, abs=0.1)
        assert response.tag.brand == "Levi's"
        assert response.tag.composition == {"cotton": 80.0, "polyester": 20.0}
        assert reasoning is not None
        assert "cotton" in reasoning["material"].lower() or "natural" in reasoning["material"].lower()
        # Grad-CAM must be null for VLM source
        assert response.material.heatmap_base64 is None
        assert response.condition.heatmap_base64 is None


# ── 2. JSON wrapped in markdown fence ────────────────────────────────────────

@pytest.mark.asyncio
async def test_markdown_fenced_json():
    """VLM wraps JSON in ```json ... ``` — should still parse correctly."""
    wrapped = "```json\n" + json.dumps(VALID_VLM_JSON) + "\n```"
    with patch("backend.app.ml.vlm._provider") as mock_provider:
        mock_provider.call = AsyncMock(return_value=wrapped)

        response, source, reasoning = await vlm_analyze([TINY_IMAGE])

        assert source == "vlm"
        assert response.material.label == "natural"


# ── 3. Invalid JSON on first attempt, valid on retry ─────────────────────────

@pytest.mark.asyncio
async def test_invalid_json_then_valid():
    """First call returns garbage, second returns valid JSON → still returns vlm result."""
    call_count = 0

    async def side_effect(images, mime_type="image/jpeg"):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "not valid json at all !!!!"
        return json.dumps(VALID_VLM_JSON)

    with patch("backend.app.ml.vlm._provider") as mock_provider:
        mock_provider.call = side_effect

        response, source, reasoning = await vlm_analyze([TINY_IMAGE])

        assert call_count == 2
        assert source == "vlm"
        assert response.material.label == "natural"


# ── 4. Invalid JSON on both attempts → stub fallback ─────────────────────────

@pytest.mark.asyncio
async def test_invalid_json_both_attempts_falls_back_to_stub():
    """Both VLM calls return unparseable JSON → graceful stub fallback."""
    with patch("backend.app.ml.vlm._provider") as mock_provider:
        mock_provider.call = AsyncMock(return_value="{ broken json {{")

        response, source, reasoning = await vlm_analyze([TINY_IMAGE])

        assert source == "stub"
        assert reasoning is None
        # Stub defaults
        assert response.material.label == "natural"
        assert response.condition.label == "gently_used"


# ── 5. Timeout / network error → stub fallback ───────────────────────────────

@pytest.mark.asyncio
async def test_timeout_falls_back_to_stub():
    """Network timeout on both attempts → stub fallback, never raises."""
    import httpx

    with patch("backend.app.ml.vlm._provider") as mock_provider:
        mock_provider.call = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

        response, source, reasoning = await vlm_analyze([TINY_IMAGE])

        assert source == "stub"
        assert reasoning is None


# ── 6. No API key → vlm_available() is False ────────────────────────────────

@pytest.mark.asyncio
async def test_missing_api_key_returns_stub():
    """When _provider is None (no API key), vlm_analyze returns stub immediately."""
    with patch("backend.app.ml.vlm._provider", None):
        response, source, reasoning = await vlm_analyze([TINY_IMAGE])

        assert source == "stub"
        assert reasoning is None


# ── 7. Confidence threshold gating ───────────────────────────────────────────

def test_low_confidence_material_becomes_uncertain():
    """material_confidence below threshold → label coerced to 'uncertain'."""
    low_conf_json = dict(VALID_VLM_JSON)
    low_conf_json["material_confidence"] = 0.30  # below default 0.60

    validated = _VLMResponse.model_validate(low_conf_json)
    response, _ = _apply_rules(validated)

    assert response.material.label == "uncertain"


# ── 8. Composition sum check ─────────────────────────────────────────────────

def test_composition_not_summing_to_100_marks_uncertain():
    """tag.composition summing outside 90-105% → composition_status 'uncertain'."""
    bad_sum_json = {
        **VALID_VLM_JSON,
        "tag": {
            **VALID_VLM_JSON["tag"],
            "composition": {"cotton": 40.0, "polyester": 20.0},  # sums to 60%
        },
    }

    validated = _VLMResponse.model_validate(bad_sum_json)
    response, comp_status = _apply_rules(validated)

    assert comp_status == "uncertain"


# ── 9. agrees_with_vision logic ──────────────────────────────────────────────

def test_agrees_with_vision_mismatch():
    """VLM says natural but tag composition is 100% polyester → agrees=False."""
    mismatch_json = {
        **VALID_VLM_JSON,
        "material_label": "natural",
        "material_confidence": 0.90,
        "tag": {
            **VALID_VLM_JSON["tag"],
            "composition": {"polyester": 100.0},
        },
    }
    validated = _VLMResponse.model_validate(mismatch_json)
    response, _ = _apply_rules(validated)

    assert response.tag.agrees_with_vision is False


# ── 10. _extract_json edge cases ─────────────────────────────────────────────

def test_extract_json_bare():
    raw = '{"key": "value"}'
    result = _extract_json(raw)
    assert result == {"key": "value"}


def test_extract_json_with_prose_prefix():
    raw = 'Here is the JSON:\n{"key": "value"}\nEnd of response.'
    result = _extract_json(raw)
    assert result == {"key": "value"}


def test_extract_json_raises_on_no_json():
    with pytest.raises((ValueError, Exception)):
        _extract_json("No JSON here at all, just prose text.")


# ── 11. Schema: invalid material_label rejected ───────────────────────────────

def test_invalid_material_label_rejected():
    bad = dict(VALID_VLM_JSON)
    bad["material_label"] = "leather"
    with pytest.raises(Exception):
        _VLMResponse.model_validate(bad)


# ── 12. Schema: invalid condition_label rejected ─────────────────────────────

def test_invalid_condition_label_rejected():
    bad = dict(VALID_VLM_JSON)
    bad["condition_label"] = "perfect"
    with pytest.raises(Exception):
        _VLMResponse.model_validate(bad)


# ── 13. No images → stub fallback ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_images_returns_stub():
    """Calling vlm_analyze with empty image list returns stub."""
    with patch("backend.app.ml.vlm._provider") as mock_provider:
        mock_provider.call = AsyncMock(return_value=json.dumps(VALID_VLM_JSON))

        response, source, reasoning = await vlm_analyze([])

        assert source == "stub"
