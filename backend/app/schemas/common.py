from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _check_bcrypt_limit(password: str) -> str:
    if len(password.encode()) > 72:
        raise ValueError("Password must be at most 72 bytes")
    return password


Email = Annotated[EmailStr, AfterValidator(normalize_email)]
NewPassword = Annotated[str, Field(min_length=8), AfterValidator(_check_bcrypt_limit)]
