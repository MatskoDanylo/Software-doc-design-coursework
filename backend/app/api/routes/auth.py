from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, auth: AuthServiceDep) -> object:
    return auth.register(data)


@router.post("/login")
def login(data: LoginRequest, auth: AuthServiceDep) -> TokenPair:
    return auth.login(data)


@router.post("/refresh")
def refresh(data: RefreshRequest, auth: AuthServiceDep) -> TokenPair:
    return auth.refresh(data.refresh_token)
