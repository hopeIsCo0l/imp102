from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.audit import log_action
from app.database import get_db
from app.deps import require_roles
from app.models import Application, Job, ParsedCV, User
from app.services.export_service import export_shortlist_csv

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


@router.get("/jobs/{job_id}/rank")
def rank_candidates(
    job_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("recruiter", "admin")),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role != "admin" and job.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not your job")

    apps = db.query(Application).filter(Application.job_id == job_id).all()
    out = []
    for app in apps:
        app.final_score = (app.cv_score * job.cv_weight) + (app.exam_score * job.exam_weight)
        parsed = db.query(ParsedCV).filter(ParsedCV.application_id == app.id).first()
        out.append(
            {
                "application_id": app.id,
                "candidate_id": app.candidate_id,
                "cv_score": round(app.cv_score, 2),
                "exam_score": round(app.exam_score, 2),
                "final_score": round(app.final_score, 2),
                "top_skills": (parsed.top_skills if parsed else ""),
            }
        )
    db.commit()
    out.sort(key=lambda x: x["final_score"], reverse=True)
    log_action(db, user.id, "rank_candidates", f"job_id={job_id}")
    return {"job_id": job_id, "shortlist": out}


@router.get("/jobs/{job_id}/export")
def export_shortlist(
    job_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("recruiter", "admin")),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role != "admin" and job.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    file_path = export_shortlist_csv(db, job_id)
    log_action(db, user.id, "export_shortlist", f"job_id={job_id}")
    return FileResponse(file_path, media_type="text/csv", filename=file_path.split("/")[-1])
