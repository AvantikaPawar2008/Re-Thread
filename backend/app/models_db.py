"""SQLAlchemy ORM models for RE-THREAD.

Represents database tables for:
- Brands (takeback policies)
- Facilities (drop-off partners)
- PathwayRules (deterministic eligibility rules)
- ImpactFactors (LCA water & CO2 factors)
- Recommendations (generated options & QR tracking)
- Outcomes (QR confirmed intake events)
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    aliases = Column(String(255), nullable=True)  # Comma-separated aliases for fuzzy OCR matching
    takeback_active = Column(Boolean, default=False, nullable=False)
    takeback_terms = Column(Text, nullable=True)
    accepted_materials = Column(String(100), default="all")  # e.g. "all", "natural,synthetic"
    notes = Column(Text, nullable=True)


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    facility_type = Column(String(50), nullable=False)  # 'donation', 'repair', 'recycling', 'brand_store'
    address = Column(String(255), nullable=False)
    city = Column(String(50), default="Pune", nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    contact_phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    accepted_materials = Column(String(100), default="all")
    accepted_conditions = Column(String(100), default="all")
    notes = Column(Text, nullable=True)

    outcomes = relationship("Outcome", back_populates="facility")


class PathwayRule(Base):
    __tablename__ = "pathway_rules"

    id = Column(Integer, primary_key=True, index=True)
    pathway = Column(String(50), nullable=False, index=True)  # 'reuse_resell', 'repair', 'donate', 'recycle', 'brand_takeback'
    min_condition = Column(String(50), default="worn")  # minimum required condition
    max_damage_percent = Column(Float, default=100.0)  # max tolerable damage %
    eligible_materials = Column(String(100), default="all")
    requires_brand_partner = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class ImpactFactor(Base):
    __tablename__ = "impact_factors"

    id = Column(Integer, primary_key=True, index=True)
    pathway = Column(String(50), nullable=False, index=True)
    material_type = Column(String(50), nullable=False, index=True)  # 'natural', 'synthetic', 'blend'
    water_litres_saved_per_kg = Column(Float, nullable=False)
    co2_kg_saved_per_kg = Column(Float, nullable=False)
    source_citation = Column(String(255), nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    qr_id = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    user_lat = Column(Float, nullable=True)
    user_lon = Column(Float, nullable=True)
    analysis_json = Column(Text, nullable=False)  # Serialized AnalyzeResponse
    recommended_pathway = Column(String(50), nullable=False)
    ranked_pathways_json = Column(Text, nullable=False)  # Serialized RankedPathway list
    explanation = Column(Text, nullable=False)
    is_scanned = Column(Boolean, default=False, nullable=False)

    outcomes = relationship("Outcome", back_populates="recommendation")


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, index=True)
    qr_id = Column(String(64), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True)
    scanned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    partner_facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    confirmed_pathway = Column(String(50), nullable=False)
    partner_notes = Column(Text, nullable=True)

    recommendation = relationship("Recommendation", back_populates="outcomes")
    facility = relationship("Facility", back_populates="outcomes")
