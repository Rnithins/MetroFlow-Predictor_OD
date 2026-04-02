from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import get_settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str | Any, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")
