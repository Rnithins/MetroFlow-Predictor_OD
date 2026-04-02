from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.api.deps import get_current_user, get_db
from app.schemas.auth import UserPublic
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.documents import utc_now, with_public_id

router = APIRouter(prefix="/profile", tags=["profile"])


def _public_user(user: dict) -> UserPublic:
    return UserPublic(**with_public_id(user))


@router.get("", response_model=ProfileResponse)
def get_profile(current_user: dict = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse(user=_public_user(current_user))


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    updates = {key: value for key, value in payload.model_dump().items() if value is not None}
    if not updates:
        return ProfileResponse(user=_public_user(current_user))

    updates["updated_at"] = utc_now()
    db.users.update_one({"_id": current_user["_id"]}, {"$set": updates})
    refreshed_user = db.users.find_one({"_id": current_user["_id"]})
    if refreshed_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return ProfileResponse(user=_public_user(refreshed_user))
