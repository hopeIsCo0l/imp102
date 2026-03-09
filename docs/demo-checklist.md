# EAA Recruit Demo Checklist

## Environment
- [ ] `docker compose up --build` starts frontend, backend, redis, worker.
- [ ] API health endpoint returns `{"status":"ok"}`.

## Candidate Flow
- [ ] Register candidate.
- [ ] Login candidate.
- [ ] View published jobs.
- [ ] Submit CV application.
- [ ] Confirm application status transitions to `PARSED`.
- [ ] Start and submit exam.
- [ ] View explainable report.

## Recruiter Flow
- [ ] Register/login recruiter.
- [ ] Create job with valid weights.
- [ ] Publish job.
- [ ] View ranked shortlist endpoint.
- [ ] Export shortlist CSV.

## Admin Flow
- [ ] Register/login admin.
- [ ] List users endpoint works.
- [ ] List audit logs endpoint works.

## Known Limitations (Prototype)
- OCR is placeholder through text decoding fallback.
- Exam grading uses lightweight rule matching.
- Rate limiting uses in-memory bucket (single-node only).
