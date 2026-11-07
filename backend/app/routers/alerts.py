from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import log_action
from app.database import get_db
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/alerts", tags=["Alert Management"])


@router.get("", response_model=list[schemas.AlertOut])
def list_alerts(
    severity: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(models.Alert)
    if severity:
        query = query.filter(models.Alert.severity == severity)
    if status_filter:
        query = query.filter(models.Alert.status == status_filter)
    if search:
        query = query.join(models.DetectionResult).join(models.SecurityEvent).filter(
            (models.SecurityEvent.source_ip.contains(search)) | (models.SecurityEvent.user_id.contains(search))
        )
    return query.order_by(models.Alert.created_at.desc()).all()


@router.get("/{alert_id}", response_model=schemas.AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    alert = db.get(models.Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/acknowledge", response_model=schemas.AlertOut)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(models.UserRole.ADMIN, models.UserRole.ANALYST)),
):
    alert = db.get(models.Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = models.AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by = user.id
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    log_action(db, user.id, "alert_acknowledged", f"Alert #{alert.id} acknowledged by '{user.username}'")
    return alert


@router.post("/{alert_id}/escalate", response_model=schemas.IncidentOut)
def escalate_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(models.UserRole.ADMIN, models.UserRole.ANALYST)),
):
    alert = db.get(models.Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.incident:
        raise HTTPException(status_code=400, detail="Alert already escalated to an incident")

    alert.status = models.AlertStatus.ESCALATED
    incident = models.Incident(
        alert_id=alert.id, title=f"Incident: {alert.title}", description=alert.description,
        status=models.IncidentStatus.OPEN, assigned_to=user.id,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    log_action(db, user.id, "incident_created", f"Alert #{alert.id} escalated to incident #{incident.id}")
    return incident
