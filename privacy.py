"""Privacy-safe projection for donor matching results.

Exact donor coordinates stay server-side. The UI receives a coarse map cell
(rounded to 2 decimals) plus distance so it can visualize a useful area without
exposing a precise home/location point.
"""


def public_donor_view(donor: dict) -> dict:
    allowed = (
        "donor_id", "name", "blood_group", "age", "distance_km",
        "is_available_now", "response_rate", "avg_response_time_min",
        "ml_response_probability", "compatibility_score", "match_reasons",
        "medical_screening", "image_url",
    )
    view = {key: donor[key] for key in allowed if key in donor}
    if donor.get("latitude") is not None and donor.get("longitude") is not None:
        view["map_lat"] = round(float(donor["latitude"]), 2)
        view["map_lon"] = round(float(donor["longitude"]), 2)
    return view
