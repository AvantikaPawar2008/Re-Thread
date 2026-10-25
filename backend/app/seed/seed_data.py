"""Database Seeding Script.

Loads realistic sample data from CSV files in backend/app/seed/ into
the configured database (SQLite or PostgreSQL).
"""

import csv
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.db import Base, SessionLocal, engine
from backend.app.models_db import Brand, Facility, ImpactFactor, PathwayRule

logger = logging.getLogger("seed")
logging.basicConfig(level=logging.INFO)

SEED_DIR = Path(__file__).resolve().parent


def seed_brands(db: Session) -> int:
    csv_file = SEED_DIR / "brands.csv"
    if not csv_file.exists():
        logger.warning(f"File not found: {csv_file}")
        return 0

    count = 0
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = db.query(Brand).filter(Brand.name == row["name"]).first()
            if not existing:
                brand = Brand(
                    name=row["name"],
                    aliases=row.get("aliases"),
                    takeback_active=row["takeback_active"].strip().lower() in ("true", "1", "yes"),
                    takeback_terms=row.get("takeback_terms"),
                    accepted_materials=row.get("accepted_materials", "all"),
                    notes=row.get("notes"),
                )
                db.add(brand)
                count += 1
    db.commit()
    logger.info(f"Seeded {count} brands.")
    return count


def seed_facilities(db: Session) -> int:
    csv_file = SEED_DIR / "facilities.csv"
    if not csv_file.exists():
        logger.warning(f"File not found: {csv_file}")
        return 0

    count = 0
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = db.query(Facility).filter(Facility.name == row["name"]).first()
            if not existing:
                facility = Facility(
                    name=row["name"],
                    facility_type=row["facility_type"],
                    address=row["address"],
                    city=row.get("city", "Pune"),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    contact_phone=row.get("contact_phone"),
                    website=row.get("website"),
                    accepted_materials=row.get("accepted_materials", "all"),
                    accepted_conditions=row.get("accepted_conditions", "all"),
                    notes=row.get("notes"),
                )
                db.add(facility)
                count += 1
    db.commit()
    logger.info(f"Seeded {count} facilities.")
    return count


def seed_impact_factors(db: Session) -> int:
    csv_file = SEED_DIR / "impact_factors.csv"
    if not csv_file.exists():
        logger.warning(f"File not found: {csv_file}")
        return 0

    count = 0
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = (
                db.query(ImpactFactor)
                .filter(
                    ImpactFactor.pathway == row["pathway"],
                    ImpactFactor.material_type == row["material_type"],
                )
                .first()
            )
            if not existing:
                factor = ImpactFactor(
                    pathway=row["pathway"],
                    material_type=row["material_type"],
                    water_litres_saved_per_kg=float(row["water_litres_saved_per_kg"]),
                    co2_kg_saved_per_kg=float(row["co2_kg_saved_per_kg"]),
                    source_citation=row["source_citation"],
                )
                db.add(factor)
                count += 1
    db.commit()
    logger.info(f"Seeded {count} impact factors.")
    return count


def seed_rules(db: Session) -> int:
    csv_file = SEED_DIR / "rules.csv"
    if not csv_file.exists():
        logger.warning(f"File not found: {csv_file}")
        return 0

    count = 0
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = (
                db.query(PathwayRule)
                .filter(PathwayRule.pathway == row["pathway"])
                .first()
            )
            if not existing:
                rule = PathwayRule(
                    pathway=row["pathway"],
                    min_condition=row.get("min_condition", "worn"),
                    max_damage_percent=float(row.get("max_damage_percent", 100.0)),
                    eligible_materials=row.get("eligible_materials", "all"),
                    requires_brand_partner=row.get("requires_brand_partner", "false").strip().lower() in ("true", "1", "yes"),
                    is_active=row.get("is_active", "true").strip().lower() in ("true", "1", "yes"),
                    notes=row.get("notes"),
                )
                db.add(rule)
                count += 1
    db.commit()
    logger.info(f"Seeded {count} pathway rules.")
    return count


def seed_all():
    """Create all tables and seed with CSV initial datasets."""
    logger.info("Creating database tables if not existing...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_brands(db)
        seed_facilities(db)
        seed_impact_factors(db)
        seed_rules(db)
        logger.info("Database seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
