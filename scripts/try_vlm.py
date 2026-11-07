#!/usr/bin/env python
"""scripts/try_vlm.py — Run VLM perception on one image from the command line.

Usage:
    python scripts/try_vlm.py path/to/garment.jpg [path/to/tag.jpg]

Requirements:
    - VLM_API_KEY and VLM_PROVIDER set in .env (or as environment variables)
    - pip install httpx python-dotenv pillow

The script prints the full JSON analysis result to stdout.
"""

import asyncio
import json
import sys
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env before importing settings
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from backend.app.ml.vlm import initialize_vlm, vlm_analyze, vlm_available


async def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: python scripts/try_vlm.py <garment_image> [tag_image]", file=sys.stderr)
        sys.exit(1)

    garment_path = Path(args[0])
    if not garment_path.exists():
        print(f"Error: file not found: {garment_path}", file=sys.stderr)
        sys.exit(1)

    tag_path = Path(args[1]) if len(args) > 1 else None
    if tag_path and not tag_path.exists():
        print(f"Error: tag file not found: {tag_path}", file=sys.stderr)
        sys.exit(1)

    # Initialise VLM
    initialize_vlm()

    if not vlm_available():
        print(
            "ERROR: VLM is not configured.\n"
            "Set VLM_API_KEY (and optionally VLM_PROVIDER, VLM_MODEL) in your .env file.\n"
            "See .env.example for details.",
            file=sys.stderr,
        )
        sys.exit(1)

    garment_bytes = garment_path.read_bytes()
    tag_bytes = tag_path.read_bytes() if tag_path else None

    print(f"Sending {garment_path.name}"
          + (f" + {tag_path.name}" if tag_path else "")
          + " to VLM...\n")

    response, source, reasoning = await vlm_analyze([garment_bytes], tag_bytes)

    output = {
        "source": source,
        "material": {
            "label": response.material.label,
            "confidence": response.material.confidence,
        },
        "condition": {
            "label": response.condition.label,
            "confidence": response.condition.confidence,
        },
        "damage": {
            "detected": response.damage.detected,
            "area_percent": response.damage.area_percent,
            "boxes": [
                {"x1": b.x1, "y1": b.y1, "x2": b.x2, "y2": b.y2, "label": b.label}
                for b in response.damage.boxes
            ],
        },
        "tag": {
            "brand": response.tag.brand,
            "composition": response.tag.composition,
            "ocr_confidence": response.tag.ocr_confidence,
            "agrees_with_vision": response.tag.agrees_with_vision,
        },
        "composition_status": response.composition_status,
        "reasoning": reasoning,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

