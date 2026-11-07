"""Rule-based craft recommender.

How it works (and what it does *not* do)
----------------------------------------
Recommendations come from a hand-written catalog
(``data/craft_ideas.json``). Each idea declares which garment categories it
suits. The recommender maps the model-predicted label to a catalog category
(by exact key, then synonym, then a conservative whole-word match) and returns
the ideas that declare that category.

It does **not** infer fabric composition, weight, colour or condition from the
photo. If the trained models predict a label that the catalog does not know,
only generic "any soft fabric" ideas are returned and the result says so via
``match = "universal"``.

When the two models disagree, only ideas that suit *every* candidate category
are returned (``match = "shared"``), falling back to generic ideas.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.fabric import decision as dec

DATA_FILE = Path(__file__).resolve().parent / "data" / "craft_ideas.json"

DIFFICULTIES = ("Easy", "Medium", "Advanced")
_DIFFICULTY_RANK = {d: i for i, d in enumerate(DIFFICULTIES)}
_SEWING_VALUES = {"none", "hand", "machine"}

# Match reasons (stable API contract)
MATCH_CATEGORY = "category"   # idea explicitly lists the predicted category
MATCH_SHARED = "shared"       # suits every candidate category (models disagreed)
MATCH_UNIVERSAL = "universal"  # generic idea; no category match was possible


class CatalogError(ValueError):
    """The craft catalog file is malformed."""


@dataclass(frozen=True)
class Recommendation:
    idea: Dict[str, Any]
    match: str  # one of MATCH_*


@dataclass(frozen=True)
class RecommendationSet:
    basis: str                       # one of MATCH_* (dominant reason)
    category: Optional[str]          # resolved catalog category, if any
    candidate_categories: List[str]  # resolved categories for disagreement
    unresolved_labels: List[str]     # model labels the catalog does not know
    items: List[Recommendation]
    note: str                        # plain-language description of how these were chosen


# ---------------------------------------------------------------------------
# Catalog loading and validation
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_catalog() -> Dict[str, Any]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    _validate_catalog(catalog)
    return catalog


def _validate_catalog(catalog: Dict[str, Any]) -> None:
    categories = catalog.get("categories")
    ideas = catalog.get("ideas")
    if not isinstance(categories, dict) or not categories:
        raise CatalogError("catalog 'categories' must be a non-empty object")
    if not isinstance(ideas, list) or not ideas:
        raise CatalogError("catalog 'ideas' must be a non-empty list")

    for key, cat in categories.items():
        for field in ("display", "synonyms", "typical_weight_kg"):
            if field not in cat:
                raise CatalogError(f"category '{key}' missing '{field}'")
        if not (isinstance(cat["typical_weight_kg"], (int, float)) and cat["typical_weight_kg"] > 0):
            raise CatalogError(f"category '{key}' has invalid typical_weight_kg")

    seen = set()
    for idea in ideas:
        iid = idea.get("id")
        if not iid or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", iid):
            raise CatalogError(f"invalid idea id: {iid!r}")
        if iid in seen:
            raise CatalogError(f"duplicate idea id: {iid}")
        seen.add(iid)
        if idea.get("difficulty") not in DIFFICULTIES:
            raise CatalogError(f"idea '{iid}' has invalid difficulty")
        if idea.get("sewing") not in _SEWING_VALUES:
            raise CatalogError(f"idea '{iid}' has invalid sewing value")
        t = idea.get("time_minutes")
        if not (isinstance(t, list) and len(t) == 2 and 0 < t[0] <= t[1]):
            raise CatalogError(f"idea '{iid}' has invalid time_minutes")
        b = idea.get("budget_inr")
        if not (isinstance(b, list) and len(b) == 2 and 0 <= b[0] <= b[1]):
            raise CatalogError(f"idea '{iid}' has invalid budget_inr")
        if len(idea.get("steps", [])) < 3:
            raise CatalogError(f"idea '{iid}' needs at least 3 steps")
        if not idea.get("materials"):
            raise CatalogError(f"idea '{iid}' needs materials")
        applies = idea.get("applies_to")
        if not applies:
            raise CatalogError(f"idea '{iid}' needs applies_to")
        for a in applies:
            if a != "any" and a not in categories:
                raise CatalogError(f"idea '{iid}' references unknown category '{a}'")


def _public_idea(idea: Dict[str, Any]) -> Dict[str, Any]:
    """Return an idea in the shape exposed by the API."""
    out = dict(idea)
    out["image"] = f"/ideas/{idea['id']}.svg"
    out.setdefault("optional_materials", [])
    out.setdefault("caveat", None)
    return out


def list_categories() -> Dict[str, Dict[str, Any]]:
    return load_catalog()["categories"]


def get_idea(idea_id: str) -> Optional[Dict[str, Any]]:
    for idea in load_catalog()["ideas"]:
        if idea["id"] == idea_id:
            return _public_idea(idea)
    return None


def list_ideas(
    *,
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Browse the whole catalog (used by the "Explore creative ideas" page)."""
    out = []
    q = (query or "").strip().lower()
    for idea in load_catalog()["ideas"]:
        if difficulty and idea["difficulty"].lower() != difficulty.lower():
            continue
        if category and category != "all":
            if category not in idea["applies_to"] and "any" not in idea["applies_to"]:
                continue
        if q:
            hay = " ".join([idea["name"], idea["tagline"], " ".join(idea["materials"])]).lower()
            if q not in hay:
                continue
        out.append(_public_idea(idea))
    return out


# ---------------------------------------------------------------------------
# Label -> catalog category
# ---------------------------------------------------------------------------
def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def normalize_category(label: Optional[str]) -> Optional[str]:
    """Map a model class label to a catalog category key, or ``None``.

    Order: exact key -> exact synonym -> whole-word match of a key or synonym
    inside the label (so "denim_jacket" resolves to ``denim``). Anything else is
    unknown; we never guess.
    """
    if not label:
        return None
    cats = list_categories()
    norm = _norm(label)
    if not norm:
        return None

    for key in cats:
        if norm == _norm(key):
            return key
    for key, cat in cats.items():
        if norm in {_norm(s) for s in cat["synonyms"]}:
            return key

    tokens = f" {norm} "
    best: Optional[str] = None
    best_len = 0
    for key, cat in cats.items():
        for term in [key, *cat["synonyms"]]:
            t = _norm(term)
            if t and f" {t} " in tokens and len(t) > best_len:
                best, best_len = key, len(t)
    return best


def category_display(key: Optional[str]) -> Optional[str]:
    if key is None:
        return None
    return list_categories().get(key, {}).get("display")


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------
def _sorted(ideas: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Stable: easier ideas first, otherwise catalog order.
    return sorted(ideas, key=lambda i: _DIFFICULTY_RANK[i["difficulty"]])


def _suits(idea: Dict[str, Any], category: str) -> bool:
    return "any" in idea["applies_to"] or category in idea["applies_to"]


def _universal(ideas: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [i for i in ideas if "any" in i["applies_to"]]


def recommend(
    status: str,
    final_label: Optional[str],
    candidates: Sequence[str],
    limit: Optional[int] = None,
) -> RecommendationSet:
    """Return craft ideas appropriate to a decision result."""
    ideas = load_catalog()["ideas"]
    cands = [c for c in candidates if c]
    if final_label and final_label not in cands:
        cands = [final_label, *cands]

    resolved: List[Optional[str]] = [normalize_category(c) for c in cands]
    unresolved = [c for c, r in zip(cands, resolved) if r is None]
    known = []
    for r in resolved:
        if r is not None and r not in known:
            known.append(r)

    items: List[Recommendation]
    basis: str
    category: Optional[str] = None
    note: str

    if status == dec.DISAGREEMENT:
        if known and all(r is not None for r in resolved):
            shared = [i for i in ideas if all(_suits(i, k) for k in known)]
            if len(known) == 1:
                # Different labels but the same catalog category: no real conflict for crafting.
                category = known[0]
                explicit = [i for i in shared if category in i["applies_to"]]
                rest = [i for i in shared if i not in explicit]
                items = [Recommendation(_public_idea(i), MATCH_CATEGORY) for i in _sorted(explicit)]
                items += [Recommendation(_public_idea(i), MATCH_UNIVERSAL) for i in _sorted(rest)]
                basis = MATCH_CATEGORY
                note = (
                    "The two models used different labels that map to the same catalog "
                    f"category ('{category}'), so ideas for that category are shown."
                )
            else:
                explicit = [i for i in shared if "any" not in i["applies_to"]]
                rest = [i for i in shared if "any" in i["applies_to"]]
                items = [Recommendation(_public_idea(i), MATCH_SHARED) for i in _sorted(explicit)]
                items += [Recommendation(_public_idea(i), MATCH_UNIVERSAL) for i in _sorted(rest)]
                basis = MATCH_SHARED
                note = (
                    "The models disagree, so only ideas that suit every candidate "
                    "category are shown."
                )
        else:
            known = []
            items = [Recommendation(_public_idea(i), MATCH_UNIVERSAL) for i in _sorted(_universal(ideas))]
            basis = MATCH_UNIVERSAL
            note = (
                "The models disagree and at least one predicted label is not in the "
                "recipe catalog, so only generic ideas for any soft fabric are shown."
            )
        if not items:  # no overlap at all -> generic ideas
            items = [Recommendation(_public_idea(i), MATCH_UNIVERSAL) for i in _sorted(_universal(ideas))]
            basis = MATCH_UNIVERSAL
            note += " No idea suits every candidate, so generic ideas are shown instead."

    elif status == dec.UNCERTAIN or not final_label:
        items = [Recommendation(_public_idea(i), MATCH_UNIVERSAL) for i in _sorted(_universal(ideas))]
        basis = MATCH_UNIVERSAL
        known = []
        note = (
            "The model's confidence was too low to assert a category, so only generic "
            "ideas for any soft fabric are shown."
        )

    else:
        category = known[0] if known else None
        if category:
            explicit = [i for i in ideas if category in i["applies_to"]]
            rest = [i for i in _universal(ideas) if i not in explicit]
            items = [Recommendation(_public_idea(i), MATCH_CATEGORY) for i in _sorted(explicit)]
            items += [Recommendation(_public_idea(i), MATCH_UNIVERSAL) for i in _sorted(rest)]
            basis = MATCH_CATEGORY
            note = (
                f"Matched to the catalog category '{category}'. Ideas that specifically "
                "list it come first, followed by generic ideas."
            )
        else:
            items = [Recommendation(_public_idea(i), MATCH_UNIVERSAL) for i in _sorted(_universal(ideas))]
            basis = MATCH_UNIVERSAL
            note = (
                f"The predicted label '{final_label}' is not in the recipe catalog, so only "
                "generic ideas for any soft fabric are shown."
            )

    if limit is not None:
        items = items[:limit]

    return RecommendationSet(
        basis=basis,
        category=category,
        candidate_categories=known,
        unresolved_labels=unresolved,
        items=items,
        note=note,
    )