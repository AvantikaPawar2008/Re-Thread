"""Care Tag Text Parsing & Vision Cross-Checking Module.

Extracts fiber composition using regex against a fixed textile vocabulary,
performs fuzzy brand matching with RapidFuzz, verifies percentage integrity (sum ~100%),
and cross-checks against the primary vision material prediction.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from rapidfuzz import process, fuzz

from backend.app.schemas import CompositionStatus, MaterialLabel, TagAnalysis

logger = logging.getLogger("ml.tag.parse")

# Fixed Fiber Vocabulary categorized into natural, synthetic, and regenerated
NATURAL_FIBERS: Set[str] = {
    "cotton", "wool", "silk", "linen", "flax", "hemp",
    "jute", "cashmere", "mohair", "alpaca", "ramie"
}

SYNTHETIC_FIBERS: Set[str] = {
    "polyester", "nylon", "polyamide", "acrylic", "elastane",
    "spandex", "lycra", "polyurethane", "polypropylene"
}

REGENERATED_FIBERS: Set[str] = {
    "viscose", "rayon", "modal", "lyocell", "tencel", "acetate", "cupro"
}

ALL_KNOWN_FIBERS = NATURAL_FIBERS | SYNTHETIC_FIBERS | REGENERATED_FIBERS

# Fiber alias normalization mapping
FIBER_SYNONYMS: Dict[str, str] = {
    "polyamide": "nylon",
    "spandex": "elastane",
    "lycra": "elastane",
    "flax": "linen",
    "rayon": "viscose",
}

# Known Fashion Brands and Aliases for Fuzzy Matching
BRAND_ALIASES: Dict[str, str] = {
    "h&m": "H&M",
    "hm": "H&M",
    "hennes & mauritz": "H&M",
    "hennes and mauritz": "H&M",
    "zara": "Zara",
    "zara basic": "Zara",
    "inditex": "Zara",
    "marks & spencer": "Marks & Spencer",
    "marks and spencer": "Marks & Spencer",
    "m&s": "Marks & Spencer",
    "levi's": "Levi's",
    "levis": "Levi's",
    "levi strauss": "Levi's",
    "levi strauss & co": "Levi's",
    "fabindia": "Fabindia",
    "fab india": "Fabindia",
    "decathlon": "Decathlon",
    "quechua": "Decathlon",
    "kalenji": "Decathlon",
    "domyos": "Decathlon",
    "raymond": "Raymond",
    "park avenue": "Raymond",
    "colorplus": "Raymond",
    "patagonia": "Patagonia",
    "worn wear": "Patagonia",
    "uniqlo": "Uniqlo",
    "nike": "Nike",
    "adidas": "Adidas",
    "puma": "Puma",
    "gap": "Gap",
    "mango": "Mango",
    "max fashion": "Max Fashion",
    "westside": "Westside",
    "pantaloons": "Pantaloons",
}


def match_brand(ocr_text_block: str) -> Optional[str]:
    """Fuzzy match care tag text against known fashion brands and aliases using RapidFuzz."""
    lines = [line.strip() for line in ocr_text_block.split("\n") if line.strip()]
    if not lines:
        return None

    best_match_key = None
    best_score = 0.0

    alias_keys = list(BRAND_ALIASES.keys())

    for line in lines:
        # Check token_set_ratio on the line against known aliases
        res = process.extractOne(
            line,
            alias_keys,
            scorer=fuzz.token_set_ratio,
            processor=lambda s: s.lower(),
            score_cutoff=70.0,
        )
        if res:
            matched_key, score, _ = res
            if score > best_score:
                best_score = score
                best_match_key = matched_key

    if best_match_key:
        return BRAND_ALIASES[best_match_key]

def extract_fiber_composition(ocr_text_block: str) -> Tuple[Dict[str, float], bool]:
    """Extract fiber percentages using regex matching against fixed vocabulary.

    Checks if extracted percentages sum to approximately 100% (90% to 105%).
    Returns (composition_dict, parse_succeeded).
    """
    composition: Dict[str, float] = {}

    # Regex pattern 1: "60% Cotton" or "60 % Polyester"
    p1 = re.compile(r"(\d{1,3})\s*%\s*([a-zA-Z\s]+)")
    # Regex pattern 2: "Cotton 60%" or "Polyester 40%"
    p2 = re.compile(r"([a-zA-Z\s]+)\s*(\d{1,3})\s*%")

    lines = ocr_text_block.split("\n")
    for line in lines:
        clean_line = line.strip().lower()
        if not clean_line:
            continue

        # Try pattern 1
        matches = p1.findall(clean_line)
        for pct_str, word_str in matches:
            words = word_str.strip().split()
            for w in words:
                norm_w = FIBER_SYNONYMS.get(w, w)
                if norm_w in ALL_KNOWN_FIBERS:
                    val = float(pct_str)
                    if 0 < val <= 100:
                        composition[norm_w] = val

        # Try pattern 2
        matches_rev = p2.findall(clean_line)
        for word_str, pct_str in matches_rev:
            words = word_str.strip().split()
            for w in words:
                norm_w = FIBER_SYNONYMS.get(w, w)
                if norm_w in ALL_KNOWN_FIBERS:
                    val = float(pct_str)
                    if 0 < val <= 100:
                        composition[norm_w] = val

    if not composition:
        return {}, False

    total_pct = sum(composition.values())
    # Percentages must sum to ~100% (tolerant between 90% and 105% for rounding/spandex blends)
    is_valid = 90.0 <= total_pct <= 105.0

    return composition, is_valid


def determine_tag_coarse_type(composition: Dict[str, float]) -> MaterialLabel:
    """Classify parsed composition into coarse natural, synthetic, or blend."""
    if not composition:
        return "uncertain"

    has_natural = any(f in NATURAL_FIBERS for f in composition)
    has_synthetic = any(f in SYNTHETIC_FIBERS for f in composition)
    has_regenerated = any(f in REGENERATED_FIBERS for f in composition)

    # Any mixed natural + synthetic/regenerated is a blend
    if (has_natural and has_synthetic) or (has_natural and has_regenerated) or len(composition) > 1:
        # If it has 95%+ of one fiber, treat as that fiber
        for f, pct in composition.items():
            if pct >= 95.0:
                if f in NATURAL_FIBERS:
                    return "natural"
                elif f in SYNTHETIC_FIBERS:
                    return "synthetic"
        return "blend"

    if has_natural:
        return "natural"
    if has_synthetic or has_regenerated:
        return "synthetic"

    return "uncertain"


def parse_tag_and_crosscheck(
    ocr_lines: List[Tuple[str, float]],
    vision_material: MaterialLabel,
) -> Tuple[TagAnalysis, CompositionStatus]:
    """Parse OCR output lines, extract brand & composition, and cross-check with vision.

    Gracefully handles missing or unreadable tags (Rule #6).
    """
    if not ocr_lines:
        # Missing or unreadable tag fallback
        tag_result = TagAnalysis(
            brand=None,
            composition={},
            ocr_confidence=0.0,
            agrees_with_vision=True,
        )
        status: CompositionStatus = "uncertain" if vision_material == "uncertain" else "confident"
        return tag_result, status

    ocr_text_block = "\n".join([line for line, _ in ocr_lines])
    avg_confidence = round(sum(conf for _, conf in ocr_lines) / max(1, len(ocr_lines)), 2)

    # 1. Fuzzy Brand Matching
    matched_brand = match_brand(ocr_text_block)

    # 2. Extract Fiber Composition and Verify Sum ~100%
    composition, sum_valid = extract_fiber_composition(ocr_text_block)

    # 3. Cross-Check with Vision
    if not sum_valid or not composition:
        # Parse failed (percentages didn't sum to 100 or unreadable)
        agrees = True  # Cannot contradict
        composition_status: CompositionStatus = "uncertain" if vision_material == "uncertain" else "confident"
    else:
        tag_material = determine_tag_coarse_type(composition)

        if vision_material == "uncertain":
            agrees = True
            composition_status = "uncertain"  # Surface uncertainty honestly
        elif vision_material == "blend" and tag_material in ("natural", "synthetic", "blend"):
            agrees = True
            composition_status = "confident"
        elif vision_material == tag_material:
            agrees = True
            composition_status = "confident"
        else:
            # Significant disagreement (e.g. Vision predicted natural, but tag reads 100% polyester)
            agrees = False
            composition_status = "uncertain"  # Flag uncertainty per Section 7.2

    tag_result = TagAnalysis(
        brand=matched_brand,
        composition=composition,
        ocr_confidence=avg_confidence,
        agrees_with_vision=agrees,
    )

    return tag_result, composition_status
