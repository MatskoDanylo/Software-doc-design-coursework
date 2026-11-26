from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import UserServiceDep, require_admin
from app.schemas.user import UserRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserRead])
def list_users(
    users: UserServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> object:
    return users.list_users(limit, offset)
