from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, UrlConstraints, field_validator

from app.models import Role


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str
    avatar_url: str | None
    country: str | None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role
    created_at: datetime
    profile: ProfileRead


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: Annotated[HttpUrl, UrlConstraints(max_length=500)] | None = None
    country: str | None = Field(default=None, max_length=100)

    @field_validator("display_name")
    @classmethod
    def _display_name_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("display_name cannot be null")
        return value
