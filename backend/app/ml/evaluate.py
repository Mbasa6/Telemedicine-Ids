"""Trains both detection models on a held-out split of the labelled synthetic dataset and records
evaluation metrics to ml_models/evaluation_results.json."""
import json
import os
import time

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from app.config import settings
from app.ml.if_model import IsolationForestDetector
from app.ml.preprocessing import extract_features
from app.ml.rf_model import RandomForestDetector


def run_full_evaluation(dataset_path: str) -> dict:
    df = pd.read_csv(dataset_path, parse_dates=["timestamp"])
    df["is_attack"] = (df["attack_label"].str.lower() != "normal").astype(int)

    X, feature_names = extract_features(df)
    y = df["is_attack"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    rf_path = os.path.join(settings.ML_MODELS_DIR, "random_forest_model.joblib")
    rf = RandomForestDetector(rf_path)
    rf.train(X_train, y_train, feature_names)
    rf.save()

    start = time.perf_counter()
    y_pred, _y_prob = rf.predict(X_test)
    latency_ms = ((time.perf_counter() - start) / max(len(X_test), 1)) * 1000

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    false_positive_rate = fp / (fp + tn) if (fp + tn) else 0.0

    rf_metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "false_positive_rate": round(float(false_positive_rate), 4),
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": ["normal(0)", "attack(1)"],
        "avg_prediction_latency_ms": round(latency_ms, 4),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
    }

    # Isolation Forest trained only on rows labelled "normal" within the TRAINING split to avoid data leakage
    normal_train_mask = y_train == 0
    if_path = os.path.join(settings.ML_MODELS_DIR, "isolation_forest_model.joblib")
    iso = IsolationForestDetector(if_path)
    iso.train(X_train[normal_train_mask])
    iso.save()

    anomaly_scores_test = iso.anomaly_scores(X_test)
    anomaly_flagged = (anomaly_scores_test >= 0.5).astype(int)
    iso_metrics = {
        "trained_on_normal_only_rows": int(normal_train_mask.sum()),
        "mean_anomaly_score_normal_test": round(
            float(anomaly_scores_test[y_test == 0].mean()) if (y_test == 0).any() else 0.0, 4
        ),
        "mean_anomaly_score_attack_test": round(
            float(anomaly_scores_test[y_test == 1].mean()) if (y_test == 1).any() else 0.0, 4
        ),
        "flagged_rate_test": round(float(anomaly_flagged.mean()), 4),
        "note": (
            "Isolation Forest is unsupervised; metrics above describe score separation between known "
            "classes for evaluation purposes only. It identifies deviations from learned normal behaviour, "
            "not a guarantee of detecting every unknown attack type."
        ),
    }

    results = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "dataset_path": dataset_path,
        "dataset_rows": int(len(df)),
        "feature_names": feature_names,
        "random_forest": rf_metrics,
        "isolation_forest": iso_metrics,
    }

    os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)
    with open(os.path.join(settings.ML_MODELS_DIR, "evaluation_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    return results
