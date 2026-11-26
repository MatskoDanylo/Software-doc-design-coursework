from fastapi import APIRouter

from app.api.deps import CurrentUser, SubscriptionServiceDep, UserServiceDep
from app.models import User
from app.schemas.subscription import SubscriptionRead
from app.schemas.user import MeRead, ProfileUpdate, UserRead
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_me(user: CurrentUser, subscriptions: SubscriptionServiceDep) -> MeRead:
    return _me(user, subscriptions)


@router.patch("/me")
def update_me(
    data: ProfileUpdate, user: CurrentUser, users: UserServiceDep, subscriptions: SubscriptionServiceDep
) -> MeRead:
    return _me(users.update_profile(user, data), subscriptions)


def _me(user: User, subscriptions: SubscriptionService) -> MeRead:
    return MeRead(
        **UserRead.model_validate(user).model_dump(),
        subscription=SubscriptionRead.model_validate(subscriptions.summary(user.id)),
    )
