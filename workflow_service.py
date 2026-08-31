"""End-to-end request workflow service.

Keeps workflow logic separate from Flask routes so it can later be consumed
by a web/mobile client or a background notification worker.
"""
from datetime import datetime, timezone

from notifications import donor_match_message, send_notification

OUTCOMES = {"accepted", "declined", "no_response", "completed"}


def build_match_summary(match_result: dict) -> dict:
    matches = match_result.get("matches", [])
    return {
        "request_id": match_result.get("request_id"),
        "matches_found": len(matches),
        "top_match": matches[0] if matches else None,
        "model_version": match_result.get("model_version"),
        "data_source": match_result.get("data_source"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def prepare_donor_notifications(matches: list[dict], blood_group: str, urgency: str) -> list[dict]:
    """Prepare consent-aware notifications without claiming delivery."""
    prepared = []
    for rank, donor in enumerate(matches, 1):
        if not donor.get("is_available_now"):
            continue
        prepared.append({
            "donor_id": donor["donor_id"],
            "rank": rank,
            "message": donor_match_message(blood_group, urgency, float(donor.get("distance_km", 0))),
            "notification_status": "requires_authenticated_consent",
        })
    return prepared


def validate_outcome(value: str) -> str:
    value = str(value or "").strip().lower()
    if value not in OUTCOMES:
        raise ValueError(f"Outcome must be one of: {', '.join(sorted(OUTCOMES))}")
    return value
