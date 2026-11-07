"""Decision rule that combines the ResNet50 and NASNet predictions.

Design principles
-----------------
* **No score averaging.** The two networks have different calibration, so their
  softmax confidences are not on a comparable scale. The rule only compares
  *labels*, and uses each model's own confidence solely as a gate against a
  configurable threshold.
* **Disagreement is surfaced, not resolved.** When the models pick different
  classes there is no final label. Both candidates are reported and the
  recommender is told to use only ideas that suit *both*.
* **Confidence is not accuracy.** A softmax score says how peaked the model's
  output is, not how often it is right. This module never reports accuracy;
  verified accuracy comes only from a held-out evaluation report (see
  ``ml/evaluate_fabric_models.py``).

This rule (``agreement-gate-v1``) is a conservative heuristic. It has NOT been
validated on data, because no dataset or trained weights ship with the
repository. ``ml/evaluate_fabric_models.py`` measures how often the models
agree and how accurate agreed predictions are, which is the evidence needed to
justify (or replace) this rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

RULE_ID = "agreement-gate-v1"

# Decision status values (stable API contract)
AGREEMENT = "agreement"                # both models, same label, both >= threshold
WEAK_AGREEMENT = "weak_agreement"      # both models, same label, >=1 below threshold
DISAGREEMENT = "disagreement"          # both models, different labels
SINGLE_MODEL = "single_model"          # only one model available, >= threshold
UNCERTAIN = "uncertain"                # only one model available, below threshold


@dataclass(frozen=True)
class Prediction:
    """One model's top-1 prediction plus its top-k distribution slice."""

    model: str                 # "resnet50" | "nasnet"
    label: str
    confidence: float          # softmax probability of ``label`` in [0, 1]
    top_k: Tuple[Tuple[str, float], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Decision:
    status: str
    final_label: str | None          # None when no single label can be asserted
    candidates: Tuple[str, ...]      # labels the recommender should consider
    low_confidence: bool
    threshold: float
    summary: str                     # plain-language explanation
    rule_id: str = RULE_ID


def decide(predictions: Sequence[Prediction], threshold: float) -> Decision:
    """Apply the documented rule to the available model predictions.

    ``predictions`` must contain only models that actually produced an output.
    Passing an empty sequence is a programming error (the API returns a
    "models unavailable" error before this point).
    """
    preds: List[Prediction] = list(predictions)
    if not preds:
        raise ValueError("decide() requires at least one model prediction")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be within [0, 1]")

    if len(preds) == 1:
        p = preds[0]
        name = _display(p.model)
        if p.confidence >= threshold:
            return Decision(
                status=SINGLE_MODEL,
                final_label=p.label,
                candidates=(p.label,),
                low_confidence=False,
                threshold=threshold,
                summary=(
                    f"Only {name} was available, so this result could not be "
                    f"cross-checked against a second model. {name} predicts "
                    f"'{p.label}'."
                ),
            )
        return Decision(
            status=UNCERTAIN,
            final_label=None,
            candidates=(p.label,),
            low_confidence=True,
            threshold=threshold,
            summary=(
                f"Only {name} was available and its confidence "
                f"({p.confidence:.0%}) is below the {threshold:.0%} threshold, "
                f"so no category is asserted. Its best guess was '{p.label}'."
            ),
        )

    a, b = preds[0], preds[1]
    if a.label == b.label:
        weak = a.confidence < threshold or b.confidence < threshold
        if weak:
            return Decision(
                status=WEAK_AGREEMENT,
                final_label=a.label,
                candidates=(a.label,),
                low_confidence=True,
                threshold=threshold,
                summary=(
                    f"Both models predict '{a.label}', but at least one is below "
                    f"the {threshold:.0%} confidence threshold. Treat this as a "
                    "tentative category and check it against your garment."
                ),
            )
        return Decision(
            status=AGREEMENT,
            final_label=a.label,
            candidates=(a.label,),
            low_confidence=False,
            threshold=threshold,
            summary=(
                f"Both models independently predict '{a.label}'. Agreement "
                "between two models is encouraging but does not guarantee the "
                "prediction is correct."
            ),
        )

    # Different labels: report the disagreement, assert nothing.
    return Decision(
        status=DISAGREEMENT,
        final_label=None,
        candidates=(a.label, b.label),
        low_confidence=True,
        threshold=threshold,
        summary=(
            f"The models disagree: {_display(a.model)} predicts '{a.label}' "
            f"while {_display(b.model)} predicts '{b.label}'. No single category "
            "is asserted. Ideas shown are limited to those suitable for both."
        ),
    )


def _display(model_key: str) -> str:
    return {"resnet50": "ResNet50", "nasnet": "NASNet"}.get(model_key, model_key)