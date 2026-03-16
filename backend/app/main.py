from pathlib import Path
from time import time

import redis
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.routes import admin, applications, auth, exams, jobs, recruiter

Base.metadata.create_all(bind=engine)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.export_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_origin_regex=settings.cors_allow_origin_regex,
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


def _db_ready() -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def _redis_ready() -> tuple[bool, str]:
    client = redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        if client.ping():
            return True, "ok"
        return False, "ping failed"
    except Exception as exc:
        return False, str(exc)
    finally:
        client.close()


def _readiness_payload() -> tuple[dict, int]:
    db_ok, db_detail = _db_ready()
    redis_ok, redis_detail = _redis_ready()
    ready = db_ok and redis_ok
    payload = {
        "status": "ok" if ready else "degraded",
        "checks": {
            "database": {"ok": db_ok, "detail": db_detail},
            "redis": {"ok": redis_ok, "detail": redis_detail},
        },
    }
    return payload, 200 if ready else 503


@app.get("/live")
def live():
    return {"status": "ok"}


@app.get("/health")
def health():
    payload, status_code = _readiness_payload()
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/ready")
def ready():
    payload, status_code = _readiness_payload()
    return JSONResponse(status_code=status_code, content=payload)
