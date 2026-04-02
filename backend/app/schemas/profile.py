from pydantic import BaseModel, ConfigDict, Field

from app.schemas.auth import UserPublic


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=80)
    job_title: str | None = Field(default=None, max_length=80)
    organization: str | None = Field(default=None, max_length=120)
    commute_line: str | None = Field(default=None, max_length=40)
    theme_preference: str | None = Field(default=None, pattern="^(light|dark|system)$")


class ProfileResponse(BaseModel):
    user: UserPublic
