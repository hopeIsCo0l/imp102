from celery import Celery
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.ai_pipeline import parse_and_score_application

celery_app = Celery("eaa_worker", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(
    name="parse_cv_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def parse_cv_task(application_id: int):
    db: Session = SessionLocal()
    try:
        parse_and_score_application(db, application_id)
    finally:
        db.close()
