from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)
    role: str = "candidate"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    class Config:
        from_attributes = True


class JobCreateIn(BaseModel):
    title: str
    description: str
    required_skills: str = ""
    cv_weight: float = 0.6
    exam_weight: float = 0.4
    deadline: str
    status: str = "DRAFT"


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    required_skills: str
    cv_weight: float
    exam_weight: float
    deadline: str
    status: str
    created_by: int

    class Config:
        from_attributes = True


class ApplicationOut(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    resume_filename: str
    status: str
    cv_score: float
    exam_score: float
    final_score: float
    submitted_at: datetime

    class Config:
        from_attributes = True


class ExamSubmitIn(BaseModel):
    answers: str


class ReportOut(BaseModel):
    application_id: int
    explanation_text: str
    top_skills: Optional[str] = ""
