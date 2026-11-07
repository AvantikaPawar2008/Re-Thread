"""Catalog validity and recommendation relevance."""

import copy
import json

import pytest

from backend.app.fabric import decision as d
from backend.app.fabric import recommender as rec
from backend.app.fabric.recommender import CatalogError


def ids(rs):
    return [i.idea["id"] for i in rs.items]


# ---------------------------------------------------------------- catalog
def test_catalog_loads_and_is_valid():
    cat = rec.load_catalog()
    assert len(cat["ideas"]) >= 12
    assert set(rec.DIFFICULTIES) >= {i["difficulty"] for i in cat["ideas"]}


def test_every_difficulty_level_is_represented():
    present = {i["difficulty"] for i in rec.load_catalog()["ideas"]}
    assert present == set(rec.DIFFICULTIES)


def test_every_category_has_at_least_two_dedicated_or_universal_ideas():
    for cat in rec.list_categories():
        rs = rec.recommend(d.AGREEMENT, cat, [cat])
        assert len(rs.items) >= 2, cat


def test_each_idea_has_card_fields():
    for idea in rec.list_ideas():
        for f in ("name", "difficulty", "materials", "time_minutes", "steps", "budget_inr", "image"):
            assert idea[f], (idea["id"], f)
        assert idea["image"] == f"/ideas/{idea['id']}.svg"


@pytest.mark.parametrize(
    "mutate,msg",
    [
        (lambda c: c["ideas"][0].update(difficulty="Hard"), "difficulty"),
        (lambda c: c["ideas"][0].update(applies_to=["spaceship"]), "unknown category"),
        (lambda c: c["ideas"][0].update(steps=["only one"]), "steps"),
        (lambda c: c["ideas"][1].update(id=c["ideas"][0]["id"]), "duplicate"),
        (lambda c: c["ideas"][0].update(time_minutes=[50, 10]), "time_minutes"),
    ],
)
def test_validation_catches_bad_catalogs(mutate, msg):
    cat = copy.deepcopy(rec.load_catalog())
    mutate(cat)
    with pytest.raises(CatalogError, match=msg):
        rec._validate_catalog(cat)


def test_catalog_file_is_valid_json_with_no_duplicate_keys():
    def no_dupes(pairs):
        keys = [k for k, _ in pairs]
        assert len(keys) == len(set(keys)), keys
        return dict(pairs)

    with open(rec.DATA_FILE, encoding="utf-8") as f:
        json.load(f, object_pairs_hook=no_dupes)


# --------------------------------------------------------- label mapping
@pytest.mark.parametrize(
    "label,expected",
    [
        ("denim", "denim"), ("Jeans", "denim"), ("T-Shirt", "tshirt"), ("t_shirt", "tshirt"),
        ("denim_jacket", "denim"), ("bed sheet", "bedsheet"), ("Kurta", "shirt"),
        ("sweater", "knitwear"), ("hoodie", "knitwear"),
    ],
)
def test_normalize_known_labels(label, expected):
    assert rec.normalize_category(label) == expected


@pytest.mark.parametrize("label", ["", None, "spaceship", "xyz123", "shirtless"])
def test_normalize_unknown_labels_return_none(label):
    assert rec.normalize_category(label) is None


# ---------------------------------------------------------- recommend()
def test_agreement_on_denim_returns_denim_ideas_first():
    rs = rec.recommend(d.AGREEMENT, "denim", ["denim"])
    assert rs.basis == rec.MATCH_CATEGORY and rs.category == "denim"
    first = rs.items[0]
    assert first.match == rec.MATCH_CATEGORY
    assert "denim" in first.idea["applies_to"]
    # Everything shown must actually suit denim or be generic.
    for item in rs.items:
        assert "denim" in item.idea["applies_to"] or "any" in item.idea["applies_to"]


def test_tshirt_gets_tshirt_tote_but_not_denim_organizer():
    got = ids(rec.recommend(d.AGREEMENT, "tshirt", ["tshirt"]))
    assert "tshirt-tote" in got
    assert "denim-organizer" not in got


def test_unknown_label_falls_back_to_universal_only():
    rs = rec.recommend(d.AGREEMENT, "spaceship", ["spaceship"])
    assert rs.basis == rec.MATCH_UNIVERSAL
    assert rs.unresolved_labels == ["spaceship"]
    assert rs.items and all("any" in i.idea["applies_to"] for i in rs.items)


def test_uncertain_returns_universal_ideas_only():
    rs = rec.recommend(d.UNCERTAIN, None, ["denim"])
    assert rs.basis == rec.MATCH_UNIVERSAL
    assert all("any" in i.idea["applies_to"] for i in rs.items)


def test_disagreement_returns_only_ideas_that_suit_both():
    rs = rec.recommend(d.DISAGREEMENT, None, ["denim", "trousers"])
    assert rs.basis == rec.MATCH_SHARED
    assert rs.candidate_categories == ["denim", "trousers"]
    assert rs.items
    for item in rs.items:
        a = item.idea["applies_to"]
        assert "any" in a or ("denim" in a and "trousers" in a)


def test_disagreement_with_no_overlap_uses_generic_ideas():
    rs = rec.recommend(d.DISAGREEMENT, None, ["towel", "denim"])
    assert rs.basis in (rec.MATCH_SHARED, rec.MATCH_UNIVERSAL)
    for item in rs.items:
        a = item.idea["applies_to"]
        assert "any" in a or ("towel" in a and "denim" in a)


def test_disagreement_with_unknown_label_is_generic():
    rs = rec.recommend(d.DISAGREEMENT, None, ["denim", "spaceship"])
    assert rs.basis == rec.MATCH_UNIVERSAL
    assert all("any" in i.idea["applies_to"] for i in rs.items)


def test_disagreement_synonyms_of_same_category_are_not_a_conflict():
    rs = rec.recommend(d.DISAGREEMENT, None, ["jeans", "denim"])
    assert rs.category == "denim" and rs.basis == rec.MATCH_CATEGORY


def test_limit_and_difficulty_ordering():
    rs = rec.recommend(d.AGREEMENT, "shirt", ["shirt"], limit=3)
    assert len(rs.items) == 3
    full = rec.recommend(d.AGREEMENT, "shirt", ["shirt"])
    explicit = [i for i in full.items if i.match == rec.MATCH_CATEGORY]
    ranks = [rec.DIFFICULTIES.index(i.idea["difficulty"]) for i in explicit]
    assert ranks == sorted(ranks)


def test_recommend_is_deterministic():
    a = ids(rec.recommend(d.AGREEMENT, "dress", ["dress"]))
    b = ids(rec.recommend(d.AGREEMENT, "dress", ["dress"]))
    assert a == b


def test_list_ideas_filters():
    easy = rec.list_ideas(difficulty="easy")
    assert easy and all(i["difficulty"] == "Easy" for i in easy)
    denim = rec.list_ideas(category="denim")
    assert any(i["id"] == "jeans-tote" for i in denim)
    assert all("denim" in i["applies_to"] or "any" in i["applies_to"] for i in denim)
    assert rec.list_ideas(query="scrunchie")
    assert rec.list_ideas(query="zzzz-not-there") == []


def test_get_idea():
    assert rec.get_idea("tshirt-tote")["name"]
    assert rec.get_idea("nope") is None