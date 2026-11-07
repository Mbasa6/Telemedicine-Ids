import json
import os

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import log_action
from app.config import settings
from app.database import get_db
from app.ml.evaluate import run_full_evaluation
from app.ml.if_model import IsolationForestDetector
from app.ml.preprocessing import extract_features
from app.ml.rf_model import RandomForestDetector
from app.ml.risk_scoring import asset_criticality, build_explanation, classify_severity, compute_risk_score, normalize_frequency
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/detection", tags=["Threat Detection"])

RF_PATH = os.path.join(settings.ML_MODELS_DIR, "random_forest_model.joblib")
IF_PATH = os.path.join(settings.ML_MODELS_DIR, "isolation_forest_model.joblib")


def _events_to_df(events: list[models.SecurityEvent]) -> pd.DataFrame:
    return pd.DataFrame([{
        "timestamp": e.timestamp, "source_ip": e.source_ip, "destination_ip": e.destination_ip,
        "user_id": e.user_id, "login_attempts": e.login_attempts,
        "failed_login_attempts": e.failed_login_attempts, "request_frequency": e.request_frequency,
        "session_duration": e.session_duration, "data_transfer_volume": e.data_transfer_volume,
        "access_type": e.access_type, "device_information": e.device_information,
    } for e in events])


@router.post("/run", response_model=schemas.DetectionRunSummary)
def run_detection(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(models.UserRole.ADMIN, models.UserRole.ANALYST)),
):
    already_scored_ids = {r.event_id for r in db.query(models.DetectionResult.event_id).all()}
    query = db.query(models.SecurityEvent)
    if already_scored_ids:
        query = query.filter(~models.SecurityEvent.id.in_(already_scored_ids))
    events = query.all()

    if not events:
        return schemas.DetectionRunSummary(events_processed=0, alerts_generated=0, severity_breakdown={})

    rf = RandomForestDetector(RF_PATH)
    iso = IsolationForestDetector(IF_PATH)
    if not rf.load() or not iso.load():
        raise HTTPException(
            status_code=409,
            detail="Detection models are not trained yet. Call POST /detection/train (administrator) before running detection.",
        )

    df = _events_to_df(events)
    X, _ = extract_features(df)
    rf_preds, rf_probs = rf.predict(X)
    anomaly_scores = iso.anomaly_scores(X)

    severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    alerts_generated = 0

    for event, pred, prob, anomaly in zip(events, rf_preds, rf_probs, anomaly_scores):
        criticality = asset_criticality(event.access_type)
        freq_norm = normalize_frequency(event.request_frequency)
        risk = compute_risk_score(float(prob), float(anomaly), criticality, freq_norm)
        severity = classify_severity(risk)
        explanation = build_explanation(float(prob), float(anomaly), criticality, freq_norm, risk, severity)

        result = models.DetectionResult(
            event_id=event.id, random_forest_prediction=int(pred), attack_probability=float(prob),
            anomaly_score=float(anomaly), risk_score=risk, severity=severity, detection_explanation=explanation,
        )
        db.add(result)
        db.flush()
        severity_breakdown[severity] += 1

        if severity in ("critical", "high", "medium"):
            alert = models.Alert(
                detection_result_id=result.id,
                title=f"{severity.upper()} risk activity from {event.source_ip}",
                description=explanation,
                severity=severity, risk_score=risk, status=models.AlertStatus.OPEN,
            )
            db.add(alert)
            alerts_generated += 1

    db.commit()
    log_action(db, user.id, "threat_detection_run", f"Processed {len(events)} events, generated {alerts_generated} alerts")

    return schemas.DetectionRunSummary(
        events_processed=len(events), alerts_generated=alerts_generated, severity_breakdown=severity_breakdown,
    )


@router.post("/train")
def train_models(db: Session = Depends(get_db), admin: models.User = Depends(require_roles(models.UserRole.ADMIN))):
    dataset_path = os.path.join(os.path.dirname(settings.ML_MODELS_DIR), "data", "synthetic_telemedicine_events.csv")
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail=f"Training dataset not found at {dataset_path}")
    try:
        results = run_full_evaluation(dataset_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model training/evaluation failed: {exc}")
    log_action(
        db, admin.id, "model_training",
        f"Retrained Random Forest + Isolation Forest on {results['dataset_rows']} labelled rows",
    )
    return results


@router.get("/evaluation")
def get_evaluation(user: models.User = Depends(get_current_user)):
    eval_path = os.path.join(settings.ML_MODELS_DIR, "evaluation_results.json")
    if not os.path.exists(eval_path):
        raise HTTPException(status_code=404, detail="No evaluation results yet. Train the models first.")
    with open(eval_path) as f:
        return json.load(f)


@router.get("/results", response_model=list[schemas.DetectionResultOut])
def list_results(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.DetectionResult)
        .order_by(models.DetectionResult.created_at.desc())
        .offset(skip)
        .limit(min(limit, 1000))
        .all()
    )
