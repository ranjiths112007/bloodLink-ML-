"""Train and evaluate the BloodLink donor-response ranking model.

Current fallback data is synthetic. When real interaction logs exist, provide a
CSV with the same feature columns plus `label` and set BLOODLINK_DATA=path.csv.
The saved bundle contains metrics and a clear model version so the UI/API can
avoid presenting synthetic performance as clinical validation.
"""

import json
import os
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from generate_training_data import generate

FEATURES = [
    "distance_km", "days_since_last_donation", "is_first_time_donor", "age",
    "past_donations", "response_rate", "avg_response_time_min", "is_available_now",
]


def load_data():
    path = os.getenv("BLOODLINK_DATA")
    if path and os.path.exists(path):
        return pd.read_csv(path), "real"
    return generate(), "synthetic"


def main():
    df, data_source = load_data()
    missing = [c for c in FEATURES + ["label"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    X, y = df[FEATURES], df["label"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=400, max_depth=8, min_samples_leaf=5,
        random_state=42, class_weight="balanced", n_jobs=-1,
    )
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "pr_auc": round(float(average_precision_score(y_test, probabilities)), 4),
        "rows": int(len(df)),
        "positive_rate": round(float(y.mean()), 4),
    }

    print("Data source:", data_source)
    print("Metrics:", json.dumps(metrics, indent=2))
    print(classification_report(y_test, predictions))

    importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print("Feature importances:\n", importances)

    version = f"{data_source}-rf-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    bundle = {
        "model": model,
        "features": FEATURES,
        "model_version": version,
        "data_source": data_source,
        "metrics": metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(bundle, "donor_response_model.joblib")
    with open("model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(bundle | {"model": None, "features": FEATURES}, f, indent=2, default=str)
    print(f"Saved model -> donor_response_model.joblib ({version})")


if __name__ == "__main__":
    main()
