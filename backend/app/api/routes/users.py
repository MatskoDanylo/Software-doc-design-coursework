from fastapi import APIRouter

from app.api.deps import CurrentUser, UserServiceDep
from app.schemas.user import ProfileUpdate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(user: CurrentUser) -> object:
    return user


@router.patch("/me", response_model=UserRead)
def update_me(data: ProfileUpdate, user: CurrentUser, users: UserServiceDep) -> object:
    return users.update_profile(user, data)
