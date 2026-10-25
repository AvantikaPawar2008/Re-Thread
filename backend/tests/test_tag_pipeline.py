"""Unit tests for Phase 6: Care Tag Pipeline (OpenCV Cleaning, RapidFuzz, & Regex Parsing)."""

import io
import numpy as np
from PIL import Image
import pytest

from backend.app.ml.tag.clean import clean_tag_image
from backend.app.ml.tag.parse import (
    determine_tag_coarse_type,
    extract_fiber_composition,
    match_brand,
    parse_tag_and_crosscheck,
)
from backend.app.schemas import TagAnalysis


# ---------------------------------------------------------------------------
# 1. OpenCV Preprocessing Tests (Deskew, CLAHE, Binarization)
# ---------------------------------------------------------------------------
def test_clean_tag_image_produces_valid_bytes():
    """Verify that clean_tag_image processes raw image bytes and returns binary PNG bytes."""
    buf = io.BytesIO()
    # Create synthetic test image with text-like gradient
    img = Image.new("L", (150, 100), color=200)
    img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    cleaned_bytes = clean_tag_image(raw_bytes)
    assert cleaned_bytes is not None
    assert len(cleaned_bytes) > 0

    # Ensure output is decodable as an image
    cleaned_img = Image.open(io.BytesIO(cleaned_bytes))
    assert cleaned_img.size == (150, 100)


def test_clean_tag_image_empty_input():
    """Verify that empty bytes pass through safely without crashing."""
    assert clean_tag_image(b"") == b""


# ---------------------------------------------------------------------------
# 2. Fiber Composition Extraction & Percentage Sum Integrity Tests
# ---------------------------------------------------------------------------
def test_extract_fiber_composition_valid_blend():
    """Test standard blend summing to 100%."""
    sample_ocr = "H&M\n60% COTTON\n40% POLYESTER\nWASH AT 40C"
    comp, valid = extract_fiber_composition(sample_ocr)
    assert valid is True
    assert comp == {"cotton": 60.0, "polyester": 40.0}
    assert determine_tag_coarse_type(comp) == "blend"


def test_extract_fiber_composition_with_synonyms():
    """Test spandex normalized to elastane and 98/2 ratio."""
    sample_ocr = "LEVIS 501\n98% COTTON\n2% SPANDEX\nMADE IN INDIA"
    comp, valid = extract_fiber_composition(sample_ocr)
    assert valid is True
    assert "cotton" in comp
    assert "elastane" in comp
    assert comp["cotton"] == 98.0
    assert comp["elastane"] == 2.0
    # Over 95% cotton qualifies as natural
    assert determine_tag_coarse_type(comp) == "natural"


def test_extract_fiber_composition_incomplete_percentage():
    """Test corrupted or incomplete OCR text failing the 100% sum check."""
    # Only 40% detected, missing the remaining 60%
    sample_ocr = "GARMENT DETAILS\n40% POLYESTER"
    comp, valid = extract_fiber_composition(sample_ocr)
    assert valid is False  # Sum is 40%, outside 90-105% range
    assert comp == {"polyester": 40.0}


# ---------------------------------------------------------------------------
# 3. Fuzzy Brand Matching Tests with RapidFuzz
# ---------------------------------------------------------------------------
def test_match_brand_fuzzy():
    """Test fuzzy brand recognition against known brands list."""
    # Slight OCR errors or sub-brands
    assert match_brand("H&M CONSCIOUS COLLECTION") == "H&M"
    assert match_brand("ZARA BASIC WOMAN") == "Zara"
    assert match_brand("LEVI STRAUSS & CO.") == "Levi's"
    assert match_brand("FABINDIA ETHNIC COTTON") == "Fabindia"
    assert match_brand("MARKS AND SPENCER") == "Marks & Spencer"
    assert match_brand("DECATHLON SPORT") == "Decathlon"
    assert match_brand("RAYMOND TAILORED") == "Raymond"
    assert match_brand("PATAGONIA WORN WEAR") == "Patagonia"


def test_match_brand_unknown():
    """Unknown brands should return None."""
    assert match_brand("UNRECOGNIZED LOCAL BRAND 123") is None
    assert match_brand("") is None


# ---------------------------------------------------------------------------
# 4. Cross-Check with Primary Vision Prediction Tests
# ---------------------------------------------------------------------------
def test_tag_and_vision_agreement():
    """When tag composition agrees with vision prediction, agrees_with_vision is True."""
    ocr_lines = [("H&M", 0.95), ("60% COTTON", 0.92), ("40% POLYESTER", 0.90)]
    tag_res, status = parse_tag_and_crosscheck(ocr_lines, vision_material="blend")

    assert tag_res.brand == "H&M"
    assert tag_res.agrees_with_vision is True
    assert status == "confident"


def test_tag_and_vision_disagreement_flags_uncertainty():
    """When tag and vision disagree significantly, flags uncertainty per Section 7.2."""
    # Vision predicted natural (e.g. thought it was cotton), but tag reads 100% polyester
    ocr_lines = [("ZARA", 0.95), ("100% POLYESTER", 0.94)]
    tag_res, status = parse_tag_and_crosscheck(ocr_lines, vision_material="natural")

    assert tag_res.brand == "Zara"
    assert tag_res.agrees_with_vision is False  # Disagreement noted
    assert status == "uncertain"  # Composition status flagged as uncertain


def test_tag_missing_or_unreadable_degrades_gracefully():
    """When care tag is absent or unreadable, never blocks user (Rule #6)."""
    tag_res, status = parse_tag_and_crosscheck([], vision_material="natural")

    assert tag_res.brand is None
    assert tag_res.composition == {}
    assert tag_res.ocr_confidence == 0.0
    assert tag_res.agrees_with_vision is True
    assert status == "confident"
