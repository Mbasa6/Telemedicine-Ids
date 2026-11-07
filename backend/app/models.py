from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole:
    ADMIN = "administrator"
    ANALYST = "security_analyst"


class AlertStatus:
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    CLOSED = "closed"


class IncidentStatus:
    OPEN = "open"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default=UserRole.ANALYST)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source_ip = Column(String(45), nullable=False, index=True)
    destination_ip = Column(String(45), nullable=False)
    # external telemedicine platform user identifier, not a FK to the app's `users` table
    user_id = Column(String(50), nullable=False, index=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    request_frequency = Column(Float, default=0.0, nullable=False)
    session_duration = Column(Float, default=0.0, nullable=False)
    data_transfer_volume = Column(Float, default=0.0, nullable=False)
    access_type = Column(String(50))
    device_information = Column(String(100))
    geo_location = Column(String(100), nullable=True)
    # ground-truth label, only populated for synthetic/labelled data, null for live unlabelled events
    attack_label = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    detection_results = relationship("DetectionResult", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_events_timestamp_ip", "timestamp", "source_ip"),)


class DetectionResult(Base):
    __tablename__ = "detection_results"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("security_events.id"), nullable=False, index=True)
    random_forest_prediction = Column(Integer, default=0, nullable=False)  # 1 = suspicious, 0 = normal
    attack_probability = Column(Float, default=0.0, nullable=False)
    anomaly_score = Column(Float, default=0.0, nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    severity = Column(String(20), default="low", nullable=False, index=True)
    detection_explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    event = relationship("SecurityEvent", back_populates="detection_results")
    alert = relationship("Alert", back_populates="detection_result", uselist=False, cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    detection_result_id = Column(Integer, ForeignKey("detection_results.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    severity = Column(String(20), index=True)
    risk_score = Column(Float)
    status = Column(String(20), default=AlertStatus.OPEN, nullable=False, index=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    detection_result = relationship("DetectionResult", back_populates="alert")
    incident = relationship("Incident", back_populates="alert", uselist=False)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default=IncidentStatus.OPEN, nullable=False, index=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    investigation_notes = Column(Text, default="")
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    alert = relationship("Alert", back_populates="incident")
    notes = relationship(
        "IncidentNote", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentNote.created_at"
    )


class IncidentNote(Base):
    """Append-only investigation note / status-change history for an incident (audit trail)."""

    __tablename__ = "incident_notes"

    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="notes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
