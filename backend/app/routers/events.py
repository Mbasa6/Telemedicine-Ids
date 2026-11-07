import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import log_action
from app.database import get_db
from app.ml.preprocessing import validate_and_normalize
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/events", tags=["Security Events"])


@router.post("/upload", response_model=schemas.IngestionResult)
async def upload_events(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(models.UserRole.ADMIN, models.UserRole.ANALYST)),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")

    clean_df, errors = validate_and_normalize(df)
    inserted = 0
    for _, row in clean_df.iterrows():
        db.add(models.SecurityEvent(**row.to_dict()))
        inserted += 1
    db.commit()

    log_action(
        db, user.id, "event_ingestion",
        f"Ingested CSV '{file.filename}': {inserted} valid rows, {len(errors)} errors",
    )

    return schemas.IngestionResult(
        total_rows=len(df), valid_rows=inserted, invalid_rows=len(df) - inserted, errors=errors[:100],
    )


@router.get("", response_model=list[schemas.SecurityEventOut])
def list_events(
    skip: int = 0,
    limit: int = 100,
    source_ip: str | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(models.SecurityEvent)
    if source_ip:
        query = query.filter(models.SecurityEvent.source_ip == source_ip)
    return query.order_by(models.SecurityEvent.timestamp.desc()).offset(skip).limit(min(limit, 1000)).all()


@router.get("/{event_id}", response_model=schemas.SecurityEventOut)
def get_event(event_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    event = db.get(models.SecurityEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
