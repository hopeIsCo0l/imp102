import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.audit import log_action
from app.config import settings
from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Application, Job, ParsedCV, User
from app.schemas import ApplicationOut, ReportOut
from app.services.ai_pipeline import parse_and_score_application

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/{job_id}/submit", response_model=ApplicationOut)
async def submit_application(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("candidate", "admin")),
):
    allowed = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
    suffix = Path(file.filename.lower()).suffix
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Invalid file type")

    job = db.query(Job).filter(Job.id == job_id, Job.status == "PUBLISHED").first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not open")
    exists = (
        db.query(Application)
        .filter(Application.job_id == job_id, Application.candidate_id == user.id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Already applied")

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    path = Path(settings.upload_dir) / safe_name
    content = await file.read()
    size_limit = 10 * 1024 * 1024
    if len(content) > size_limit:
        raise HTTPException(status_code=400, detail="File too large")
    path.write_bytes(content)

    app = Application(candidate_id=user.id, job_id=job_id, resume_filename=safe_name)
    db.add(app)
    db.commit()
    db.refresh(app)

    # Async queue can be wired here; sync fallback keeps prototype deterministic.
    parse_and_score_application(db, app.id)
    db.refresh(app)
    log_action(db, user.id, "submit_application", f"application_id={app.id}")
    return app


@router.get("/mine", response_model=list[ApplicationOut])
def my_applications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Application)
    if user.role == "candidate":
        q = q.filter(Application.candidate_id == user.id)
    return q.order_by(Application.id.desc()).all()


@router.get("/{application_id}/report", response_model=ReportOut)
def view_report(
    application_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role == "candidate" and app.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    parsed = db.query(ParsedCV).filter(ParsedCV.application_id == application_id).first()
    if not parsed:
        raise HTTPException(status_code=404, detail="Report not ready")
    return ReportOut(
        application_id=application_id,
        explanation_text=parsed.explanation,
        top_skills=parsed.top_skills,
    )
