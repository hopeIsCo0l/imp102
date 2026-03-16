from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import User
from app.schemas import AdminCreateUserIn, LoginIn, LoginOut, RegisterIn, Token, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate_user(email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role="candidate",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users", response_model=UserOut)
def create_user_as_admin(
    payload: AdminCreateUserIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = _authenticate_user(payload.email, payload.password, db)
    return LoginOut(access_token=create_access_token(user.email), user=user)


@router.post("/token", response_model=Token)
def token_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2 password flow uses `username`; we map it to our user email.
    user = _authenticate_user(form_data.username, form_data.password, db)
    return Token(access_token=create_access_token(user.email))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
