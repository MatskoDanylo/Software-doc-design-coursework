from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.errors import UnauthorizedError

ALGORITHM = "HS256"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def _lifetime(token_type: TokenType) -> timedelta:
    if token_type is TokenType.ACCESS:
        return timedelta(minutes=settings.access_token_minutes)
    return timedelta(days=settings.refresh_token_days)


def create_token(user_id: int, token_type: TokenType) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type.value,
        "jti": uuid4().hex,
        "iat": now,
        "exp": now + _lifetime(token_type),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: TokenType) -> int:
    invalid = UnauthorizedError("Invalid or expired token", code="invalid_token")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type.value:
            raise invalid
        return int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise invalid from exc
