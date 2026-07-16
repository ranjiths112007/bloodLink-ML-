"""
generate_training_data.py

Generates synthetic (donor, request) pair data with a realistic "did_respond_and_donate"
label, based on domain logic. This stands in for real BloodLink historical logs.

Once you have real outcome data (did the matched donor actually respond/donate?),
swap this out: just produce a CSV with the same columns and a real `label` column,
then re-run train_model.py.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

N = 6000  # number of synthetic (donor, request) interaction records

def generate():
    rows = []
    for _ in range(N):
        distance_km = np.round(np.random.exponential(scale=6.0), 2)
        distance_km = min(distance_km, 50)  # cap

        days_since_last_donation = np.random.choice(
            [np.nan] + list(range(90, 900)), p=[0.15] + [0.85 / 810] * 810
        )
        # first-time donors (nan) treated separately below

        age = int(np.random.normal(32, 10))
        age = max(18, min(65, age))

        past_donations = np.random.poisson(3)
        response_rate = np.clip(np.random.beta(2, 2), 0, 1)  # historical response rate 0-1
        avg_response_time_min = np.round(np.random.exponential(scale=25), 1)  # minutes to respond historically
        is_available_now = np.random.choice([1, 0], p=[0.7, 0.3])

        # ---- domain-logic label: probability donor responds & completes donation ----
        score = 0.5
        score -= (distance_km / 50) * 0.35          # farther = less likely
        score += (response_rate - 0.5) * 0.4         # good history = more likely
        score -= (avg_response_time_min / 60) * 0.15  # slow responders = less likely
        score += 0.15 if is_available_now else -0.15
        score += min(past_donations, 10) * 0.01       # experienced donors slightly more reliable
        score -= 0.1 if age < 20 or age > 55 else 0    # slight caution at extremes

        recency_bonus = 0.05 if (not np.isnan(days_since_last_donation) and days_since_last_donation < 200) else 0
        score += recency_bonus

        score += np.random.normal(0, 0.12)  # noise
        prob = np.clip(score, 0.02, 0.98)
        label = np.random.binomial(1, prob)

        rows.append({
            "distance_km": distance_km,
            "days_since_last_donation": -1 if np.isnan(days_since_last_donation) else days_since_last_donation,
            "is_first_time_donor": int(np.isnan(days_since_last_donation)),
            "age": age,
            "past_donations": past_donations,
            "response_rate": round(response_rate, 3),
            "avg_response_time_min": avg_response_time_min,
            "is_available_now": is_available_now,
            "label": label,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate()
    df.to_csv("training_data.csv", index=False)
    print(f"Generated {len(df)} rows -> training_data.csv")
    print(df["label"].value_counts(normalize=True))
