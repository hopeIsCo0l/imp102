from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.audit import log_action
from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Application, ExamResult, Job, User
from app.schemas import ExamSubmitIn

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("/{application_id}/start")
def start_exam(
    application_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role == "candidate" and app.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if app.cv_score < 40:
        raise HTTPException(status_code=400, detail="Not eligible for exam")
    questions = [
        {"id": 1, "q": "What is ATPL?", "expected": "airline transport pilot license"},
        {"id": 2, "q": "What is a safety checklist?", "expected": "preflight safety procedure"},
    ]
    return {"application_id": application_id, "questions": questions}


@router.post("/{application_id}/submit")
def submit_exam(
    application_id: int,
    payload: ExamSubmitIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("candidate", "admin")),
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role == "candidate" and app.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Lightweight semantic-like scoring for MVP.
    answer_text = payload.answers.lower()
    score = 0.0
    if "airline transport pilot" in answer_text:
        score += 50.0
    if "safety" in answer_text:
        score += 50.0

    result = db.query(ExamResult).filter(ExamResult.application_id == application_id).first()
    if not result:
        result = ExamResult(application_id=application_id)
        db.add(result)
    result.answers = payload.answers
    result.score = score

    job = db.query(Job).filter(Job.id == app.job_id).first()
    app.exam_score = score
    app.final_score = (app.cv_score * job.cv_weight) + (app.exam_score * job.exam_weight)
    app.status = "EXAM_COMPLETED"
    db.commit()
    log_action(db, user.id, "submit_exam", f"application_id={application_id}")
    return {"application_id": application_id, "exam_score": score, "final_score": app.final_score}
