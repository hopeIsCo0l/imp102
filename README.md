# EAA Recruit Prototype

Full-stack prototype for AI-assisted recruitment with:
- FastAPI backend + Celery worker
- React frontend
- TF-IDF + cosine CV matching
- Job posting, applications, exam scoring, shortlist export, and audit logs

## 1) Quick Start

1. Copy env file:
   - `cp .env.example .env` (or create `.env` manually on Windows)
2. Run with Docker:
   - `docker compose up --build`
3. Open:
   - Frontend: `http://localhost:5173`
   - API docs: `http://localhost:8000/docs`

## 2) Default Roles

Use registration form to create users with one of:
- `candidate`
- `recruiter`
- `admin`

## 3) Core Flows Implemented

- Auth + RBAC
- Job create/publish
- Candidate CV application submit
- CV parse + TF-IDF/cosine scoring
- Recruiter ranking and CSV export
- Basic exam flow and final score aggregation
- Explainable report endpoint
- Admin users/audit listing

## 4) API Endpoints (Key)

- `POST /auth/register`
- `POST /auth/login`
- `POST /jobs`
- `POST /jobs/{job_id}/publish`
- `POST /applications/{job_id}/submit`
- `GET /applications/mine`
- `GET /applications/{application_id}/report`
- `GET /recruiter/jobs/{job_id}/rank`
- `GET /recruiter/jobs/{job_id}/export`
- `GET /exams/{application_id}/start`
- `POST /exams/{application_id}/submit`
- `GET /admin/users`
- `GET /admin/audits`

## 5) Notes

- Current persistence uses SQLite for speed in solo prototype mode.
- Redis + Celery worker are included; CV parsing currently falls back to synchronous processing for deterministic local behavior.
- OCR and PDF-native extraction can be extended in `backend/app/services/ai_pipeline.py`.
