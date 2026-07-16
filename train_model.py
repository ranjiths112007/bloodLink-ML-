
"""
train_model.py
Trains a RandomForestClassifier to predict probability a donor will
respond AND successfully donate, given a matching request.

Run: python train_model.py
Outputs: donor_response_model.joblib
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, classification_report
import joblib

from generate_training_data import generate

FEATURES = [
    "distance_km",
    "days_since_last_donation",
    "is_first_time_donor",
    "age",
    "past_donations",
    "response_rate",
    "avg_response_time_min",
    "is_available_now",
]

def main():
    df = generate()
    X = df[FEATURES]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    preds_proba = model.predict_proba(X_test)[:, 1]
    preds = model.predict(X_test)

    print("ROC-AUC:", round(roc_auc_score(y_test, preds_proba), 4))
    print(classification_report(y_test, preds))

    importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print("\nFeature importances:")
    print(importances)

    joblib.dump({"model": model, "features": FEATURES}, "donor_response_model.joblib")
    print("\nSaved model -> donor_response_model.joblib")


if __name__ == "__main__":
    main()
