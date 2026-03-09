from pathlib import Path
from time import time

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import admin, applications, auth, exams, jobs, recruiter

Base.metadata.create_all(bind=engine)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.export_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(recruiter.router)
app.include_router(exams.router)
app.include_router(admin.router)

# Basic in-memory rate limit for prototype safety.
_rate_window = {}
_MAX_REQ = 120
_WINDOW_SECONDS = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    now = time()
    bucket = [t for t in _rate_window.get(client, []) if now - t < _WINDOW_SECONDS]
    if len(bucket) >= _MAX_REQ:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    bucket.append(now)
    _rate_window[client] = bucket
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}
