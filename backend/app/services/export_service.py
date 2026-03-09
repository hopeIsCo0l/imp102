import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Application, Job, User


def export_shortlist_csv(db: Session, job_id: int) -> str:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError("Job not found")

    Path(settings.export_dir).mkdir(parents=True, exist_ok=True)
    out_file = Path(settings.export_dir) / f"shortlist_job_{job_id}.csv"
    rows = (
        db.query(Application, User)
        .join(User, Application.candidate_id == User.id)
        .filter(Application.job_id == job_id)
        .order_by(Application.final_score.desc())
        .all()
    )

    with out_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Candidate", "Email", "CV Score", "Exam Score", "Final Score", "Status"])
        for app, user in rows:
            writer.writerow(
                [
                    user.full_name,
                    user.email,
                    round(app.cv_score, 2),
                    round(app.exam_score, 2),
                    round(app.final_score, 2),
                    app.status,
                ]
            )
    return str(out_file)
