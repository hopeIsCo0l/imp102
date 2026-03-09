# Architecture Summary

## Services
- `frontend` (React): user interface for candidate/recruiter/admin flows.
- `backend` (FastAPI): auth, job management, applications, reports, exams, exports.
- `worker` (Celery): async CV parsing hook.
- `redis`: queue broker and backend for Celery.

## Data Model
- `users`
- `jobs`
- `applications`
- `parsed_cvs`
- `exam_results`
- `reports`
- `audit_logs`

## AI Pipeline
1. Receive CV upload.
2. Normalize extracted text.
3. Build TF-IDF vectors for CV + Job text.
4. Compute cosine similarity score.
5. Extract top contributing terms.
6. Persist score and explanation for recruiter/candidate report.

## Security and Reliability Baselines
- JWT auth + RBAC.
- File type and size validation on upload.
- Request rate limiting middleware.
- Audit logging for key operations.
- Celery retry strategy for parse task failures.
