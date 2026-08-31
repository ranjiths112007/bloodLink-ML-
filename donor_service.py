"""Donor profile and availability operations."""
from datetime import datetime, timezone


def validate_donor_profile(payload):
    blood_group = str(payload.get("blood_group", "")).strip().upper()
    try:
        age = int(payload.get("age"))
    except (TypeError, ValueError):
        raise ValueError("age must be an integer")
    if not 18 <= age <= 65:
        raise ValueError("Donor age must be between 18 and 65 for this prototype")
    if not blood_group:
        raise ValueError("blood_group is required")
    return {"blood_group": blood_group, "age": age}


def availability_payload(is_available):
    return {"is_available_now": bool(is_available), "updated_at": datetime.now(timezone.utc).isoformat()}
