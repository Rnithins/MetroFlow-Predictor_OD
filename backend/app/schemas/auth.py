from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["user", "admin"] = "user"
    job_title: str | None = Field(default=None, max_length=80)
    organization: str | None = Field(default=None, max_length=120)
    commute_line: str | None = Field(default=None, max_length=40)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    job_title: str | None = None
    organization: str | None = None
    commute_line: str | None = None
    theme_preference: str = "system"
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
