from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pymongo.database import Database

from app.core.config import get_settings
from app.db.mongo import get_database

security = HTTPBearer(auto_error=False)


def get_db() -> Database:
    return get_database()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Database = Depends(get_db),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    token = credentials.credentials.strip()
    if not token or token.lower() in ("null", "undefined", "none", ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.users.find_one({"_id": user_id})
    if user is None:
        user = db.users.find_one({"email": user_id})

    if user is None or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or session expired")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Database = Depends(get_db),
) -> dict | None:
    if credentials is None or not credentials.credentials:
        return None

    token = credentials.credentials.strip()
    if not token or token.lower() in ("null", "undefined", "none", ""):
        return None

    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError:
        return None

    if not user_id:
        return None

    user = db.users.find_one({"_id": user_id})
    if user is None:
        user = db.users.find_one({"email": user_id})

    if user and user.get("is_active", True):
        return user
    return None


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
