"""Tests for Database Models and Seeding."""

from backend.app.models_db import Brand, Facility, ImpactFactor, PathwayRule


def test_seeded_brands(db_session):
    brands = db_session.query(Brand).all()
    assert len(brands) >= 8
    brand_names = [b.name for b in brands]
    assert "H&M" in brand_names
    assert "Zara" in brand_names
    assert "Fabindia" in brand_names


def test_seeded_facilities(db_session):
    facilities = db_session.query(Facility).all()
    assert len(facilities) >= 15
    types = {f.facility_type for f in facilities}
    assert "repair" in types
    assert "donation" in types
    assert "recycling" in types
    assert "brand_store" in types


def test_seeded_impact_factors(db_session):
    factors = db_session.query(ImpactFactor).all()
    assert len(factors) >= 12
    for factor in factors:
        assert factor.water_litres_saved_per_kg > 0.0
        assert factor.co2_kg_saved_per_kg > 0.0
        assert len(factor.source_citation) > 0


def test_seeded_rules(db_session):
    rules = db_session.query(PathwayRule).all()
    assert len(rules) >= 5
    pathways = {r.pathway for r in rules}
    assert "reuse_resell" in pathways
    assert "repair" in pathways
    assert "donate" in pathways
    assert "recycle" in pathways
    assert "brand_takeback" in pathways
