"""Privacy helpers for donor-facing responses."""


def public_donor_view(donor: dict) -> dict:
    """Return only information needed to compare a donor candidate.

    Exact coordinates and private contact information stay server-side until a
    future authenticated, consented contact workflow authorizes disclosure.
    """
    allowed = (
        "donor_id", "name", "blood_group", "age", "distance_km",
        "is_available_now", "response_rate", "avg_response_time_min",
        "ml_response_probability", "compatibility_score", "match_reasons",
        "medical_screening", "image_url",
    )
    return {key: donor[key] for key in allowed if key in donor}
