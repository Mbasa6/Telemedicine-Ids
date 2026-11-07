from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import log_action
from app.database import get_db
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/incidents", tags=["Incident Management"])

VALID_STATUSES = {
    models.IncidentStatus.OPEN, models.IncidentStatus.INVESTIGATING, models.IncidentStatus.ESCALATED,
    models.IncidentStatus.RESOLVED, models.IncidentStatus.CLOSED,
}


@router.get("", response_model=list[schemas.IncidentOut])
def list_incidents(
    status_filter: str | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    query = db.query(models.Incident)
    if status_filter:
        query = query.filter(models.Incident.status == status_filter)
    return query.order_by(models.Incident.created_at.desc()).all()


@router.get("/{incident_id}", response_model=schemas.IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    incident = db.get(models.Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/{incident_id}/status", response_model=schemas.IncidentOut)
def update_status(
    incident_id: int,
    payload: schemas.IncidentStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(models.UserRole.ADMIN, models.UserRole.ANALYST)),
):
    incident = db.get(models.Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {sorted(VALID_STATUSES)}")

    incident.status = payload.status
    incident.updated_at = datetime.utcnow()
    if payload.status == models.IncidentStatus.RESOLVED:
        incident.resolved_at = datetime.utcnow()
        if payload.resolution_notes:
            incident.resolution_notes = payload.resolution_notes

    db.add(models.IncidentNote(
        incident_id=incident.id, author_id=user.id, note=f"Status changed to '{payload.status}' by {user.username}",
    ))
    db.commit()
    db.refresh(incident)
    log_action(db, user.id, "incident_status_update", f"Incident #{incident.id} -> '{payload.status}'")
    return incident


@router.post("/{incident_id}/notes", response_model=schemas.IncidentOut)
def add_note(
    incident_id: int,
    payload: schemas.IncidentNoteCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(models.UserRole.ADMIN, models.UserRole.ANALYST)),
):
    incident = db.get(models.Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.add(models.IncidentNote(incident_id=incident.id, author_id=user.id, note=payload.note))
    incident.investigation_notes = (incident.investigation_notes or "") + f"\n[{user.username}] {payload.note}"
    db.commit()
    db.refresh(incident)
    log_action(db, user.id, "incident_note_added", f"Note added to incident #{incident.id} by '{user.username}'")
    return incident
