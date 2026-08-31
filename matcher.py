"""Safety-first hybrid donor matching engine.

Hard screening rules run before ML. The model ranks only candidates that pass
those rules. ML never makes a medical eligibility decision.
"""

import os
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd

from blood_rules import is_compatible, is_eligible_by_recency, is_eligible_by_age

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "donor_response_model.joblib")
DEFAULT_MAX_DISTANCE_KM = 30.0

try:
    bundle = joblib.load(MODEL_PATH)
    MODEL = bundle["model"]
    FEATURES = bundle["features"]
    MODEL_VERSION = bundle.get("model_version", "prototype-synthetic-v1")
    MODEL_DATA_SOURCE = bundle.get("data_source", "unknown")
    MODEL_METRICS = bundle.get("metrics", {})
except Exception as exc:
    MODEL = None
    FEATURES = []
    MODEL_VERSION = "unavailable"
    MODEL_DATA_SOURCE = "unknown"
    MODEL_METRICS = {}
    MODEL_LOAD_ERROR = str(exc)


def _build_feature_row(donor: Dict) -> List[float]:
    days = donor.get("days_since_last_donation")
    first_time = 1 if days is None else 0
    days_value = -1 if days is None else float(days)
    row = {
        "distance_km": float(donor["distance_km"]),
        "days_since_last_donation": days_value,
        "is_first_time_donor": first_time,
        "age": int(donor["age"]),
        "past_donations": int(donor.get("past_donations", 0)),
        "response_rate": float(donor.get("response_rate", 0.5)),
        "avg_response_time_min": float(donor.get("avg_response_time_min", 30.0)),
        "is_available_now": int(donor.get("is_available_now", 0)),
    }
    return [row[f] for f in FEATURES]


def _why_ranked(donor: Dict, probability: float) -> List[str]:
    reasons = []
    if donor.get("is_available_now"):
        reasons.append("available_now")
    if donor.get("distance_km", 999) <= 5:
        reasons.append("very_close")
    elif donor.get("distance_km", 999) <= 10:
        reasons.append("nearby")
    if donor.get("response_rate", 0) >= 0.8:
        reasons.append("strong_response_history")
    if donor.get("avg_response_time_min", 999) <= 15:
        reasons.append("fast_responder")
    if probability >= 0.75:
        reasons.append("high_predicted_response")
    return reasons[:4] or ["eligible_candidate"]


def find_best_donors(request: Dict, donors: List[Dict], top_n=10,
                     max_distance_km=DEFAULT_MAX_DISTANCE_KM) -> Dict:
    recipient_bg = str(request.get("blood_group", "")).strip().upper()
    if recipient_bg not in {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}:
        raise ValueError("Invalid blood group")
    if max_distance_km <= 0 or max_distance_km > 500:
        raise ValueError("max_distance_km must be between 0 and 500")
    if MODEL is None:
        raise RuntimeError(f"ML model unavailable: {MODEL_LOAD_ERROR}")

    eligible, excluded = [], []
    for donor in donors:
        if not is_compatible(donor["blood_group"], recipient_bg):
            excluded.append({**donor, "excluded_reason": "blood_type_incompatible"})
        elif not is_eligible_by_age(donor.get("age")):
            excluded.append({**donor, "excluded_reason": "age_out_of_range"})
        elif not is_eligible_by_recency(donor.get("days_since_last_donation")):
            excluded.append({**donor, "excluded_reason": "too_soon_since_last_donation"})
        elif float(donor["distance_km"]) > max_distance_km:
            excluded.append({**donor, "excluded_reason": "too_far"})
        else:
            eligible.append(donor)

    if not eligible:
        return {"matches": [], "excluded": excluded, "model_version": MODEL_VERSION,
                "data_source": MODEL_DATA_SOURCE, "screened_count": len(donors),
                "eligible_count": 0, "safety_notice": "No eligible demo-screened donors were found. Final eligibility must be confirmed by an authorised blood bank or medical professional."}

    X = pd.DataFrame([_build_feature_row(d) for d in eligible], columns=FEATURES)
    probabilities = MODEL.predict_proba(X)[:, 1]
    results = []
    for donor, probability in zip(eligible, probabilities):
        distance = float(donor["distance_km"])
        proximity = max(0.0, (max_distance_km - distance) / max_distance_km)
        score = float(np.clip(float(probability) * 85.0 + proximity * 15.0, 0, 100))
        results.append({
            **donor,
            "ml_response_probability": round(float(probability), 3),
            "compatibility_score": round(score, 1),
            "match_reasons": _why_ranked(donor, float(probability)),
            "medical_screening": "passed_demo_screening",
        })

    results.sort(key=lambda item: item["compatibility_score"], reverse=True)
    return {
        "matches": results[:max(1, min(int(top_n), 50))],
        "excluded": excluded,
        "model_version": MODEL_VERSION,
        "data_source": MODEL_DATA_SOURCE,
        "model_metrics": MODEL_METRICS,
        "screened_count": len(donors),
        "eligible_count": len(eligible),
        "safety_notice": "This is a matching recommendation, not a medical clearance. Final eligibility must be confirmed by an authorised blood bank or medical professional.",
    }
