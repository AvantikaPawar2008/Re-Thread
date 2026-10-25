"""Geography calculation utilities (Haversine distance)."""

import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models_db import Facility
from backend.app.schemas import PartnerDropoff

# Pathway to facility type mapping
PATHWAY_FACILITY_TYPE_MAP = {
    "reuse_resell": "donation",      # Local thrift/donation hubs
    "repair": "repair",
    "donate": "donation",
    "recycle": "recycling",
    "brand_takeback": "brand_store",
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth in kilometers."""
    r = 6371.0  # Earth radius in kilometers

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


def find_nearest_partner(
    db: Session,
    pathway: str,
    user_lat: float,
    user_lon: float,
    brand_name: Optional[str] = None,
) -> Optional[PartnerDropoff]:
    """Find the nearest eligible drop-off facility for a given pathway in the DB."""
    facility_type = PATHWAY_FACILITY_TYPE_MAP.get(pathway)
    if not facility_type:
        return None

    query = db.query(Facility).filter(Facility.facility_type == facility_type)
    if pathway == "brand_takeback" and brand_name:
        # Match brand name in facility name or notes if applicable
        brand_facilities = [
            f for f in query.all()
            if brand_name.lower() in f.name.lower() or (f.notes and brand_name.lower() in f.notes.lower())
        ]
        facilities = brand_facilities if brand_facilities else query.all()
    else:
        facilities = query.all()

    if not facilities:
        return None

    nearest_facility = None
    min_dist = float("inf")

    for f in facilities:
        dist = haversine_distance_km(user_lat, user_lon, f.latitude, f.longitude)
        if dist < min_dist:
            min_dist = dist
            nearest_facility = f

    if not nearest_facility:
        return None

    return PartnerDropoff(
        name=nearest_facility.name,
        distance_km=min_dist,
        address=nearest_facility.address,
        contact_phone=nearest_facility.contact_phone,
    )
