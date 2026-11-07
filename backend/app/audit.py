from sqlalchemy.orm import Session

from app import models


def log_action(db: Session, user_id: int | None, action: str, description: str = "") -> None:
    entry = models.AuditLog(user_id=user_id, action=action, description=description)
    db.add(entry)
    db.commit()
