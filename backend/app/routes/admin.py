from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import AuditLog, User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role} for u in users]


@router.get("/audits")
def list_audits(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()
    return [{"id": r.id, "user_id": r.user_id, "action": r.action, "detail": r.detail} for r in rows]
