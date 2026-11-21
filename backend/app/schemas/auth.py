from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import Email, NewPassword


class RegisterRequest(BaseModel):
    email: Email
    password: NewPassword
    display_name: str | None = Field(default=None, min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
