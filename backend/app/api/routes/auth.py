from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.schemas.auth import LoginRequest, TokenResponse, UserPublic, UserRegister
from app.services.documents import new_id, utc_now, with_public_id

router = APIRouter(prefix="/auth", tags=["auth"])


def _public_user(user: dict) -> UserPublic:
    return UserPublic(**with_public_id(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Database = Depends(get_db)) -> TokenResponse:
    if db.users.find_one({"email": payload.email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    now = utc_now()
    user = {
        "_id": new_id(),
        "email": payload.email,
        "full_name": payload.full_name,
        "password_hash": get_password_hash(payload.password),
        "role": payload.role,
        "is_active": True,
        "job_title": payload.job_title,
        "organization": payload.organization,
        "commute_line": payload.commute_line,
        "theme_preference": "system",
        "created_at": now,
        "updated_at": now,
    }
    db.users.insert_one(user)
    token = create_access_token(user["_id"], user["role"])
    return TokenResponse(access_token=token, user=_public_user(user))


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserRegister, db: Database = Depends(get_db)) -> TokenResponse:
    return register(payload, db)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database = Depends(get_db)) -> TokenResponse:
    user = db.users.find_one({"email": payload.email})
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user["_id"], user["role"])
    return TokenResponse(access_token=token, user=_public_user(user))


@router.get("/me", response_model=UserPublic)
def me(current_user: dict = Depends(get_current_user)) -> UserPublic:
    return _public_user(current_user)
