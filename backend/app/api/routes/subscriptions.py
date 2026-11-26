from fastapi import APIRouter

from app.api.deps import CurrentUser, SubscriptionServiceDep
from app.schemas.subscription import SubscriptionRead

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/cancel")
def cancel_subscription(user: CurrentUser, subscriptions: SubscriptionServiceDep) -> SubscriptionRead:
    return SubscriptionRead.model_validate(subscriptions.cancel(user))
