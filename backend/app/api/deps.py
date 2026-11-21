from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.models import Role, User
from app.repositories.users import UserRepository
from app.services.auth import AuthService
from app.services.users import UserService

SessionDep = Annotated[Session, Depends(get_db, scope="function")]
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(UserRepository(session))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_auth_service(session: SessionDep, user_service: UserServiceDep) -> AuthService:
    return AuthService(UserRepository(session), user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(credentials: BearerDep, auth: AuthServiceDep) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")
    return auth.authenticate(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != Role.ADMIN:
        raise ForbiddenError("Administrator role required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
