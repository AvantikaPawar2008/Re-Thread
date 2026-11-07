"""Plain-language explanation and next steps for an analysis result.

Everything here is derived deterministically from the decision, so it can be
regenerated at any time from stored data and never invents information that
was not produced by the models.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from app.fabric import decision as dec

CONFIDENCE_NOTICE = (
    "Confidence is how strongly a model favours its top answer. It is not a "
    "measure of how often the model is right. Real accuracy can only be "
    "measured on labelled test photos the model never saw during training."
)

NO_VERIFIED_ACCURACY = (
    "No verified accuracy is available for these models, so treat every "
    "prediction as a suggestion rather than a fact."
)


def next_steps(status: str) -> List[str]:
    care = (
        "Check the care label for the real fibre content. A photo cannot reveal "
        "whether a fabric is cotton, polyester or a blend."
    )
    if status == dec.AGREEMENT:
        return [
            "Compare the predicted category with your garment to make sure it looks right.",
            care,
            "Open the reuse ideas matched to this category.",
        ]
    if status == dec.SINGLE_MODEL:
        return [
            "Compare the predicted category with your garment; only one model could check it.",
            care,
            "Open the reuse ideas matched to this category.",
        ]
    if status == dec.WEAK_AGREEMENT:
        return [
            "Treat this category as tentative and compare it with your garment.",
            "Retake the photo in daylight with the garment laid flat and filling the frame.",
            care,
            "Open the reuse ideas, or browse general ideas that suit any soft fabric.",
        ]
    if status == dec.DISAGREEMENT:
        return [
            "Decide which category is closer to your garment. The models could not agree.",
            "Retake the photo in daylight with the garment laid flat and filling the frame.",
            care,
            "Open the ideas that suit both candidate categories.",
        ]
    return [  # uncertain
        "Retake the photo in daylight with the garment laid flat and filling the frame.",
        care,
        "Browse general ideas that suit any soft fabric.",
    ]


def explain(
    decision: dec.Decision,
    category_display: Optional[str],
) -> Tuple[str, List[str]]:
    """Return ``(explanation, next_steps)``."""
    parts = [decision.summary]
    if decision.final_label and category_display:
        parts.append(f"In the recipe catalog this corresponds to: {category_display}.")
    elif decision.final_label and not category_display:
        parts.append(
            f"'{decision.final_label}' is not in the recipe catalog, so only generic "
            "ideas for any soft fabric are suggested."
        )
    return " ".join(parts), next_steps(decision.status)