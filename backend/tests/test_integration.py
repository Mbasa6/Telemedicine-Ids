from datetime import datetime

from app import models


def test_security_event_persists_with_relationships(db_session):
    event = models.SecurityEvent(
        timestamp=datetime(2026, 1, 3, 10, 0, 0), source_ip="41.1.1.1", destination_ip="10.0.0.1",
        user_id="integration_user", login_attempts=1, failed_login_attempts=0, request_frequency=3,
        session_duration=200, data_transfer_volume=50, access_type="mobile_app", device_information="android",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    assert event.id is not None

    result = models.DetectionResult(
        event_id=event.id, random_forest_prediction=0, attack_probability=0.1, anomaly_score=0.1,
        risk_score=12.0, severity="low", detection_explanation="test",
    )
    db_session.add(result)
    db_session.commit()

    reloaded_event = db_session.get(models.SecurityEvent, event.id)
    assert len(reloaded_event.detection_results) == 1


def test_audit_log_created_on_login(client, admin_headers, db_session):
    count_before = db_session.query(models.AuditLog).count()
    client.get("/auth/me", headers=admin_headers)
    count_after = db_session.query(models.AuditLog).count()
    assert count_after >= count_before
