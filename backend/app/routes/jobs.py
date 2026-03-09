from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.audit import log_action
from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Job, User
from app.schemas import JobCreateIn, JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut)
def create_job(
    payload: JobCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("recruiter", "admin")),
):
    if round(payload.cv_weight + payload.exam_weight, 5) != 1.0:
        raise HTTPException(status_code=400, detail="Weights must sum to 1.0")
    job = Job(**payload.model_dump(), created_by=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    log_action(db, user.id, "create_job", f"job_id={job.id}")
    return job


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Job).order_by(Job.id.desc()).all()


@router.post("/{job_id}/publish", response_model=JobOut)
def publish_job(
    job_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("recruiter", "admin")),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role != "admin" and job.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    job.status = "PUBLISHED"
    db.commit()
    db.refresh(job)
    log_action(db, user.id, "publish_job", f"job_id={job.id}")
    return job
