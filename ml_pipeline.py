"""Real-data-ready ML evaluation pipeline for BloodLink.

Expected CSV columns:
 distance_km, days_since_last_donation, is_first_time_donor, age,
 past_donations, response_rate, avg_response_time_min, is_available_now,
 responded

`responded` must represent an observed donor outcome from an authorised,
consented dataset. Synthetic data should not be used for production claims.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "distance_km", "days_since_last_donation", "is_first_time_donor", "age",
    "past_donations", "response_rate", "avg_response_time_min", "is_available_now",
]
TARGET = "responded"


def train(csv_path: str, output_path: str = "donor_response_model.joblib") -> dict:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(path)
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    df = df[FEATURES + [TARGET]].copy()
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df.dropna(subset=[TARGET])
    if len(df) < 50 or df[TARGET].nunique() < 2:
        raise ValueError("Need at least 50 observed rows and both outcome classes")

    X, y = df[FEATURES], df[TARGET].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, stratify=y, random_state=42)
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    pre = ColumnTransformer([("numeric", numeric, FEATURES)], remainder="drop")
    model = Pipeline([("preprocess", pre), ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced"))])
    model.fit(X_train, y_train)
    probability = model.predict_proba(X_test)[:, 1]
    metrics = {"roc_auc": round(float(roc_auc_score(y_test, probability)), 4), "pr_auc": round(float(average_precision_score(y_test, probability)), 4), "test_rows": int(len(y_test)), "train_rows": int(len(y_train))}
    bundle = {"model": model, "features": FEATURES, "model_version": "real-data-v1", "data_source": "authorised_real_dataset", "metrics": metrics}
    joblib.dump(bundle, output_path)
    metadata_path = str(Path(output_path).with_suffix(".metadata.json"))
    Path(metadata_path).write_text(json.dumps(metrics | {"model_version": "real-data-v1", "data_source": "authorised_real_dataset"}, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    csv_path = os.environ.get("BLOODLINK_REAL_DATA_PATH")
    if not csv_path:
        raise SystemExit("Set BLOODLINK_REAL_DATA_PATH to an authorised CSV dataset before training.")
    print(train(csv_path))
