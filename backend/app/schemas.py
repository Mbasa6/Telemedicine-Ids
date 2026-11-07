from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---- Auth ----
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "security_analyst"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


# ---- Security Events ----
class SecurityEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    source_ip: str
    destination_ip: str
    user_id: str
    login_attempts: int
    failed_login_attempts: int
    request_frequency: float
    session_duration: float
    data_transfer_volume: float
    access_type: Optional[str] = None
    device_information: Optional[str] = None
    geo_location: Optional[str] = None
    attack_label: Optional[str] = None
    created_at: datetime


class IngestionResult(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[str]


# ---- Detection ----
class DetectionResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    random_forest_prediction: int
    attack_probability: float
    anomaly_score: float
    risk_score: float
    severity: str
    detection_explanation: Optional[str] = None
    created_at: datetime


class DetectionRunSummary(BaseModel):
    events_processed: int
    alerts_generated: int
    severity_breakdown: dict


# ---- Alerts ----
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detection_result_id: int
    title: str
    description: Optional[str] = None
    severity: str
    risk_score: float
    status: str
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime


# ---- Incidents ----
class IncidentCreate(BaseModel):
    alert_id: int
    title: str
    description: Optional[str] = None
    assigned_to: Optional[int] = None


class IncidentNoteCreate(BaseModel):
    note: str


class IncidentNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: Optional[int] = None
    note: str
    created_at: datetime


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int
    title: str
    description: Optional[str] = None
    status: str
    assigned_to: Optional[int] = None
    investigation_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    notes: list[IncidentNoteOut] = []


class IncidentStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


# ---- Audit ----
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    action: str
    description: Optional[str] = None
    timestamp: datetime


# ---- Reports ----
class ReportSummary(BaseModel):
    total_events: int
    total_threats_detected: int
    severity_distribution: dict
    total_alerts: int
    total_incidents: int
    incident_status_breakdown: dict
    model_info: dict
    evaluation_metrics: Optional[dict] = None
