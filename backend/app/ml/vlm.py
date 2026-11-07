"""VLM (Vision-Language Model) Perception Client for RE-THREAD.

Sends garment and tag images to a VLM API (Google Gemini or OpenAI GPT-4o)
in a single call and returns a fully-parsed AnalyzeResponse with source="vlm".

Priority order (per requirement #5):
  1. Local trained weights (handled by condition/material/damage loaders)
  2. VLM API — if VLM_API_KEY is set in .env
  3. Stub — silent fallback, never crashes

Usage:
  from backend.app.ml.vlm import vlm_analyze, vlm_available
  if vlm_available():
      result = await vlm_analyze(garment_bytes_list, tag_bytes)
"""

from __future__ import annotations

import base64
import io
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image
from pydantic import BaseModel, Field, field_validator

from backend.app.config import settings
from backend.app.schemas import (
    AnalyzeResponse,
    CompositionStatus,
    ConditionAnalysis,
    ConditionLabel,
    DamageAnalysis,
    DamageBox,
    MaterialAnalysis,
    MaterialLabel,
    TagAnalysis,
)

logger = logging.getLogger("ml.vlm")

# ── Image helpers ─────────────────────────────────────────────────────────────

MAX_IMAGE_PX = 1024


def _resize_and_encode(image_bytes: bytes, fmt: str = "JPEG") -> str:
    """Resize image to max MAX_IMAGE_PX on the longest side, handle EXIF orientation, and return base64 string."""
    try:
        from PIL import ImageOps
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((MAX_IMAGE_PX, MAX_IMAGE_PX), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to resize/encode image: {e}")
        return base64.b64encode(image_bytes[:MAX_IMAGE_PX * MAX_IMAGE_PX]).decode("utf-8")


# ── Pydantic models for VLM response validation ───────────────────────────────

class _VLMTag(BaseModel):
    brand: Optional[str] = None
    composition: Dict[str, float] = Field(default_factory=dict)
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    readable: bool = False


class _VLMDamageBox(BaseModel):
    x1: float = Field(ge=0.0, le=1.0)
    y1: float = Field(ge=0.0, le=1.0)
    x2: float = Field(ge=0.0, le=1.0)
    y2: float = Field(ge=0.0, le=1.0)


class _VLMDamage(BaseModel):
    detected: bool
    area_percent: float = Field(ge=0.0, le=100.0)
    boxes: List[_VLMDamageBox] = Field(default_factory=list)
    type: Optional[str] = None


class _VLMReasoning(BaseModel):
    material: str = ""
    condition: str = ""
    damage: str = ""
    tag: str = ""


class _VLMResponse(BaseModel):
    """Strict VLM JSON response schema — validated before use."""

    material_label: str
    material_confidence: float = Field(ge=0.0, le=1.0)
    condition_label: str
    condition_confidence: float = Field(ge=0.0, le=1.0)
    damage: _VLMDamage
    tag: _VLMTag
    reasoning: _VLMReasoning = Field(default_factory=_VLMReasoning)

    @field_validator("material_label")
    @classmethod
    def _valid_material(cls, v: str) -> str:
        allowed = {"natural", "synthetic", "blend", "uncertain"}
        if v not in allowed:
            raise ValueError(f"material_label must be one of {allowed}, got '{v}'")
        return v

    @field_validator("condition_label")
    @classmethod
    def _valid_condition(cls, v: str) -> str:
        allowed = {"new", "gently_used", "worn", "heavily_worn"}
        if v not in allowed:
            raise ValueError(f"condition_label must be one of {allowed}, got '{v}'")
        return v

    @field_validator("material_confidence", "condition_confidence")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a textile analysis AI for a circular fashion platform.
Analyse the provided garment image(s) and optional care-label image.

Return ONLY a single valid JSON object — no markdown, no prose, no code fences — with exactly these keys:

{
  "material_label": "<natural|synthetic|blend|uncertain>",
  "material_confidence": <0.0-1.0>,
  "condition_label": "<new|gently_used|worn|heavily_worn>",
  "condition_confidence": <0.0-1.0>,
  "damage": {
    "detected": <true|false>,
    "area_percent": <0-100 estimate>,
    "boxes": [{"x1":0.0,"y1":0.0,"x2":0.0,"y2":0.0}],
    "type": "<tear|stain|hole|pilling|fading|none>"
  },
  "tag": {
    "brand": "<brand name or null>",
    "composition": {"<fibre>": <percent>, ...},
    "ocr_confidence": <0.0-1.0>,
    "readable": <true|false>
  },
  "reasoning": {
    "material": "<one sentence>",
    "condition": "<one sentence>",
    "damage": "<one sentence>",
    "tag": "<one sentence>"
  }
}

Rules:
- material_label "uncertain" if you cannot determine fabric type.
- condition_label reflects overall visible wear, not just one area.
- damage boxes use normalised coordinates (0.0–1.0); may be an empty list.
- tag composition percentages should ideally sum to ~100 if readable.
- If no care label is provided or readable, set tag.readable=false and tag.composition={}.
- Never output anything except the JSON object."""


# ── Provider interface ────────────────────────────────────────────────────────

class VLMProvider(ABC):
    """Swappable VLM provider interface."""

    @abstractmethod
    async def call(
        self,
        image_b64_list: List[str],
        mime_type: str = "image/jpeg",
    ) -> str:
        """Send images to the VLM. Returns raw text response."""
        ...


class GoogleGeminiProvider(VLMProvider):
    """Google Gemini multimodal provider with automatic fallback for transient 503/404 errors."""

    def __init__(self, api_key: str, model: str, timeout: float):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    async def call(self, image_b64_list: List[str], mime_type: str = "image/jpeg") -> str:
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx is required for VLM calls: pip install httpx")

        parts: List[Dict[str, Any]] = [{"text": _SYSTEM_PROMPT}]
        for b64 in image_b64_list:
            parts.append({
                "inline_data": {"mime_type": mime_type, "data": b64}
            })
        parts.append({"text": "Analyse these garment images and return the JSON."})

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        }

        # Candidate models list: configured model first, followed by known stable fallbacks
        candidates: List[str] = [self._model]
        for fallback in ("gemini-3.6-flash", "gemini-3-flash-preview"):
            if fallback not in candidates:
                candidates.append(fallback)

        last_error: Optional[Exception] = None
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for model_name in candidates:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model_name}:generateContent?key={self._api_key}"
                )
                try:
                    resp = await client.post(url, json=payload)
                    # If model is unavailable (503) or not found (404), try next candidate
                    if resp.status_code in (404, 503) and model_name != candidates[-1]:
                        logger.warning(
                            f"Gemini model '{model_name}' returned {resp.status_code}. "
                            f"Trying fallback model..."
                        )
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code in (404, 503) and model_name != candidates[-1]:
                        continue
                    raise
                except Exception as e:
                    last_error = e
                    raise

        if last_error:
            raise last_error
        raise RuntimeError("No candidate Gemini models succeeded.")


class OpenAIProvider(VLMProvider):
    """OpenAI GPT-4o / GPT-4-vision provider."""

    def __init__(self, api_key: str, model: str, timeout: float):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    async def call(self, image_b64_list: List[str], mime_type: str = "image/jpeg") -> str:
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx is required for VLM calls: pip install httpx")

        content: List[Dict[str, Any]] = [
            {"type": "text", "text": _SYSTEM_PROMPT},
        ]
        for b64 in image_b64_list:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64}", "detail": "high"},
            })
        content.append({"type": "text", "text": "Analyse and return the JSON."})

        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "max_tokens": 1024,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


# ── VLM client singleton ──────────────────────────────────────────────────────

_provider: Optional[VLMProvider] = None
_vlm_source: str = "stub"   # "vlm" | "stub"
_vlm_provider_name: str = "none"


def _build_provider() -> Optional[VLMProvider]:
    """Instantiate the configured VLM provider if an API key is available."""
    key = settings.VLM_API_KEY
    if not key:
        return None

    pname = settings.VLM_PROVIDER.lower()
    model = settings.VLM_MODEL
    timeout = settings.VLM_TIMEOUT_SECONDS

    if pname == "openai":
        logger.info(f"VLM provider: OpenAI ({model})")
        return OpenAIProvider(api_key=key, model=model, timeout=timeout)
    else:
        logger.info(f"VLM provider: Google Gemini ({model})")
        return GoogleGeminiProvider(api_key=key, model=model, timeout=timeout)


def initialize_vlm() -> None:
    """Called once at startup by the ModelRegistry."""
    global _provider, _vlm_source, _vlm_provider_name
    _provider = _build_provider()
    if _provider is None:
        _vlm_source = "stub"
        _vlm_provider_name = "none"
        logger.warning(
            "VLM_API_KEY not set — VLM perception disabled. "
            "Set VLM_API_KEY in .env to enable. See .env.example."
        )
    else:
        _vlm_source = "vlm"
        _vlm_provider_name = settings.VLM_PROVIDER.lower()
        logger.info(f"VLM client ready: provider={_vlm_provider_name}, model={settings.VLM_MODEL}")


def vlm_available() -> bool:
    """Return True if the VLM provider is configured and ready."""
    return _provider is not None


def vlm_provider_name() -> str:
    return _vlm_provider_name


# ── JSON extraction helpers ───────────────────────────────────────────────────

def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from raw VLM response text, stripping any markdown fences."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Find first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No valid JSON found in VLM response: {text[:200]!r}")


# ── Business-rule application ─────────────────────────────────────────────────

def _apply_rules(parsed: _VLMResponse) -> Tuple[AnalyzeResponse, str]:
    """Apply RE-THREAD business rules to the validated VLM output.

    Returns (AnalyzeResponse, composition_status).
    """
    # Rule #3a: material confidence threshold
    mat_label: MaterialLabel = parsed.material_label  # type: ignore[assignment]
    if parsed.material_confidence < settings.CONFIDENCE_THRESHOLD:
        mat_label = "uncertain"

    # Rule #3b: tag composition sum ~100%
    composition = parsed.tag.composition
    total_pct = sum(composition.values())
    comp_valid = bool(composition) and (90.0 <= total_pct <= 105.0)
    composition_status: CompositionStatus = "confident" if comp_valid else "uncertain"

    # Rule #3c: agrees_with_vision
    if not comp_valid or not composition:
        agrees = True
    else:
        # Classify tag material coarsely
        from backend.app.ml.tag.parse import determine_tag_coarse_type
        tag_material = determine_tag_coarse_type(composition)
        if mat_label == "uncertain":
            agrees = True
        elif mat_label == "blend" and tag_material in ("natural", "synthetic", "blend"):
            agrees = True
        elif mat_label == tag_material:
            agrees = True
        else:
            agrees = False

    # Build response — Grad-CAM is null for VLM source (Requirement #6)
    material = MaterialAnalysis(
        label=mat_label,
        confidence=round(parsed.material_confidence, 2),
        heatmap_base64=None,  # VLM: no Grad-CAM
    )
    condition = ConditionAnalysis(
        label=parsed.condition_label,  # type: ignore[arg-type]
        confidence=round(parsed.condition_confidence, 2),
        heatmap_base64=None,
    )

    dmg = parsed.damage
    boxes = [
        DamageBox(x1=b.x1, y1=b.y1, x2=b.x2, y2=b.y2, label=dmg.type or "damage", confidence=1.0)
        for b in dmg.boxes
    ]
    damage = DamageAnalysis(
        detected=dmg.detected,
        area_percent=round(dmg.area_percent, 1),
        boxes=boxes,
    )

    tag = TagAnalysis(
        brand=parsed.tag.brand,
        composition=composition,
        ocr_confidence=round(parsed.tag.ocr_confidence, 2),
        agrees_with_vision=agrees,
    )

    response = AnalyzeResponse(
        material=material,
        condition=condition,
        damage=damage,
        tag=tag,
        composition_status=composition_status,
    )
    return response, composition_status


# ── Stub fallback ─────────────────────────────────────────────────────────────

def _stub_response() -> AnalyzeResponse:
    """Return typed stub output matching docs/PROJECT.md Section 11."""
    return AnalyzeResponse(
        material=MaterialAnalysis(label="natural", confidence=0.82, heatmap_base64=None),
        condition=ConditionAnalysis(label="gently_used", confidence=0.74, heatmap_base64=None),
        damage=DamageAnalysis(
            detected=True,
            area_percent=6.5,
            boxes=[DamageBox(x1=0.35, y1=0.45, x2=0.48, y2=0.58, label="tear", confidence=0.89)],
        ),
        tag=TagAnalysis(
            brand=None,
            composition={},
            ocr_confidence=0.0,
            agrees_with_vision=True,
        ),
        composition_status="uncertain",
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def vlm_analyze(
    garment_bytes_list: List[bytes],
    tag_bytes: Optional[bytes] = None,
) -> Tuple[AnalyzeResponse, str, Optional[Dict[str, str]]]:
    """Run VLM perception on garment (+ optional tag) images.

    Returns:
        (AnalyzeResponse, source, reasoning_dict)
        source is "vlm" or "stub".
        reasoning_dict contains per-field reasoning sentences (or None for stub).
    """
    if _provider is None:
        logger.debug("VLM not configured — returning stub response.")
        return _stub_response(), "stub", None

    # Encode all images
    all_b64: List[str] = []
    for b in garment_bytes_list:
        if b:
            all_b64.append(_resize_and_encode(b))
    if tag_bytes:
        all_b64.append(_resize_and_encode(tag_bytes))

    if not all_b64:
        logger.warning("vlm_analyze called with no image bytes — returning stub.")
        return _stub_response(), "stub", None

    # Try VLM call, retry once on JSON parse failure
    raw_text: Optional[str] = None
    for attempt in range(2):
        try:
            raw_text = await _provider.call(all_b64)
            parsed_json = _extract_json(raw_text)
            validated = _VLMResponse.model_validate(parsed_json)
            response, _ = _apply_rules(validated)

            reasoning: Dict[str, str] = {
                "material": validated.reasoning.material,
                "condition": validated.reasoning.condition,
                "damage": validated.reasoning.damage,
                "tag": validated.reasoning.tag,
            }
            logger.info(
                f"VLM analysis complete (attempt {attempt + 1}): "
                f"material={response.material.label}, condition={response.condition.label}"
            )
            return response, "vlm", reasoning

        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            logger.warning(f"VLM call attempt {attempt + 1} failed: {err_msg}")
            if attempt == 0:
                logger.info("Retrying VLM call once...")
                continue
            # Both attempts failed — fall back to stub
            logger.error(
                f"VLM analysis failed after 2 attempts. "
                f"Last error: {err_msg}. Falling back to stub."
            )
            return _stub_response(), "stub", None

    # Should not be reached
    return _stub_response(), "stub", None

