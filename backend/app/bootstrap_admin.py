from app.database import Base, SessionLocal, engine
from app.models import AuditLog, User
from app.security import hash_password
from app.config import settings


def main() -> int:
    Base.metadata.create_all(bind=engine)

    email = settings.bootstrap_admin_email
    password = settings.bootstrap_admin_password
    full_name = settings.bootstrap_admin_full_name

    if not email or not password:
        print("Missing BOOTSTRAP_ADMIN_EMAIL or BOOTSTRAP_ADMIN_PASSWORD in environment.")
        return 1

    db = SessionLocal()
    try:
        existing_admin = db.query(User.id).filter(User.role == "admin").first()
        if existing_admin:
            print("Bootstrap skipped: at least one admin user already exists.")
            return 0

        existing_email = db.query(User.id).filter(User.email == email).first()
        if existing_email:
            print(f"Bootstrap aborted: email {email} already exists with a non-admin account.")
            return 1

        admin = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role="admin",
        )
        db.add(admin)
        db.flush()
        db.add(
            AuditLog(
                user_id=admin.id,
                action="bootstrap_admin",
                detail=f"Created initial admin account: {email}",
            )
        )
        db.commit()
        print(f"Initial admin created successfully: {email}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Bootstrap failed: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
