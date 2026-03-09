import os
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Application, Job, ParsedCV


def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_and_score_application(db: Session, application_id: int) -> float:
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        return 0.0
    job = db.query(Job).filter(Job.id == app.job_id).first()
    if not job:
        app.status = "FAILED"
        db.commit()
        return 0.0

    file_path = Path(settings.upload_dir) / app.resume_filename
    raw_text = ""
    if file_path.exists():
        raw_text = file_path.read_bytes().decode("utf-8", errors="ignore")

    cv_text = _clean_text(raw_text or app.resume_filename.replace("_", " "))
    jd_text = _clean_text(f"{job.title} {job.description} {job.required_skills}")
    if not cv_text:
        cv_text = "unknown candidate skills"
    if not jd_text:
        jd_text = "general role"

    vectorizer = TfidfVectorizer(max_features=3000)
    matrix = vectorizer.fit_transform([cv_text, jd_text])
    score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100.0)

    feature_names = np.array(vectorizer.get_feature_names_out())
    cv_vec = matrix[0].toarray()[0]
    jd_vec = matrix[1].toarray()[0]
    contribution = cv_vec * jd_vec
    top_idx = contribution.argsort()[-5:][::-1]
    top_skills = [feature_names[i] for i in top_idx if contribution[i] > 0]
    top_skills_str = ", ".join(top_skills) if top_skills else "no clear skills"
    explanation = f"{score:.1f}% CV match driven by {top_skills_str}"

    parsed = db.query(ParsedCV).filter(ParsedCV.application_id == app.id).first()
    if not parsed:
        parsed = ParsedCV(application_id=app.id, extracted_text=cv_text)
        db.add(parsed)
    parsed.extracted_text = cv_text
    parsed.top_skills = top_skills_str
    parsed.explanation = explanation
    parsed.quality_score = 0.9 if raw_text else 0.5

    app.cv_score = score
    app.status = "PARSED"
    app.final_score = (app.cv_score * job.cv_weight) + (app.exam_score * job.exam_weight)
    db.commit()
    return score
