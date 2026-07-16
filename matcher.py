"""
matcher.py
The hybrid donor-matching engine for BloodLink.

Pipeline:
  1. HARD FILTER (rules): blood compatibility, age eligibility, 90-day recency rule,
     max distance cutoff. A donor that fails any of these is NEVER shown, regardless
     of ML score.
  2. ML RANKING: among eligible donors, predict probability of successful response,
     using donor_response_model.joblib.
  3. FINAL SCORE (0-100): blend of ML probability + a distance bonus, so that among
     similarly "reliable" donors, closer ones still rank higher.

Usage:
    from matcher import find_best_donors
    ranked = find_best_donors(request, donors)
"""

import joblib
import numpy as np
import pandas as pd

from blood_rules import is_compatible, is_eligible_by_recency, is_eligible_by_age

import os
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_BUNDLE_PATH = os.path.join(_BASE_DIR, "donor_response_model.joblib")
_MODEL_BUNDLE = joblib.load(_MODEL_BUNDLE_PATH)
_MODEL = _MODEL_BUNDLE["model"]
_FEATURES = _MODEL_BUNDLE["features"]

MAX_DISTANCE_KM = 30  # hard cutoff; tune per city/service area


def _build_feature_row(donor):
    """donor: dict with donor fields -> feature vector in the order the model expects."""
    days_since = donor.get("days_since_last_donation")
    is_first_time = 1 if days_since is None else 0
    days_since_val = -1 if days_since is None else days_since

    row = {
        "distance_km": donor["distance_km"],
        "days_since_last_donation": days_since_val,
        "is_first_time_donor": is_first_time,
        "age": donor["age"],
        "past_donations": donor.get("past_donations", 0),
        "response_rate": donor.get("response_rate", 0.5),
        "avg_response_time_min": donor.get("avg_response_time_min", 30.0),
        "is_available_now": int(donor.get("is_available_now", 0)),
    }
    return [row[f] for f in _FEATURES]


def find_best_donors(request, donors, top_n=10, max_distance_km=MAX_DISTANCE_KM):
    """
    request: dict, must include "blood_group" (recipient's needed blood group)
    donors: list of dicts, each must include:
        donor_id, blood_group, distance_km, age,
        days_since_last_donation (or None), past_donations,
        response_rate, avg_response_time_min, is_available_now
    Returns: list of donors sorted best-first, each with an added "compatibility_score" (0-100)
             and "eligible_reason" / "excluded_reason" for transparency.
    """
    recipient_bg = request["blood_group"]
    eligible = []
    excluded = []

    for donor in donors:
        if not is_compatible(donor["blood_group"], recipient_bg):
            excluded.append({**donor, "excluded_reason": "blood_type_incompatible"})
            continue
        if not is_eligible_by_age(donor["age"]):
            excluded.append({**donor, "excluded_reason": "age_out_of_range"})
            continue
        if not is_eligible_by_recency(donor.get("days_since_last_donation")):
            excluded.append({**donor, "excluded_reason": "too_soon_since_last_donation"})
            continue
        if donor["distance_km"] > max_distance_km:
            excluded.append({**donor, "excluded_reason": "too_far"})
            continue
        eligible.append(donor)

    if not eligible:
        return {"matches": [], "excluded": excluded}

    X = pd.DataFrame([_build_feature_row(d) for d in eligible], columns=_FEATURES)
    ml_probs = _MODEL.predict_proba(X)[:, 1]  # probability of successful response

    results = []
    for donor, prob in zip(eligible, ml_probs):
        distance_bonus = max(0, (max_distance_km - donor["distance_km"]) / max_distance_km) * 15
        final_score = np.clip(prob * 85 + distance_bonus, 0, 100)
        results.append({
            **donor,
            "ml_response_probability": round(float(prob), 3),
            "compatibility_score": round(float(final_score), 1),
        })

    results.sort(key=lambda d: d["compatibility_score"], reverse=True)
    return {"matches": results[:top_n], "excluded": excluded}


if __name__ == "__main__":
    # quick smoke test
    request = {"blood_group": "O+"}
    donors = [
        {"donor_id": 1, "blood_group": "O-", "distance_km": 3.2, "age": 27,
         "days_since_last_donation": 120, "past_donations": 5,
         "response_rate": 0.9, "avg_response_time_min": 8, "is_available_now": 1},
        {"donor_id": 2, "blood_group": "AB+", "distance_km": 2.0, "age": 30,
         "days_since_last_donation": 400, "past_donations": 1,
         "response_rate": 0.4, "avg_response_time_min": 60, "is_available_now": 0},
        {"donor_id": 3, "blood_group": "O+", "distance_km": 15.0, "age": 45,
         "days_since_last_donation": 40, "past_donations": 10,
         "response_rate": 0.7, "avg_response_time_min": 20, "is_available_now": 1},
    ]
    result = find_best_donors(request, donors)
    for m in result["matches"]:
        print(m["donor_id"], m["compatibility_score"], m["ml_response_probability"])
    print("Excluded:", [(e["donor_id"], e["excluded_reason"]) for e in result["excluded"]])
