from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(db: Session, user_id: int, action: str, detail: str = "") -> None:
    db.add(AuditLog(user_id=user_id, action=action, detail=detail))
    db.commit()
