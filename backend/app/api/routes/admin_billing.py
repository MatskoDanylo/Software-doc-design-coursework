from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import BillingServiceDep, SubscriptionServiceDep, UserServiceDep, require_admin
from app.models import PaymentStatus, PlanCode
from app.schemas.billing import AdminPaymentPage, AdminPaymentRead, ResolveRequest, SubscriptionChange
from app.schemas.subscription import SubscriptionRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/payments")
def list_payments(
    billing: BillingServiceDep,
    status: PaymentStatus | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AdminPaymentPage:
    items, total = billing.payments_page(status, page, page_size)
    return AdminPaymentPage(
        items=[AdminPaymentRead.from_payment(p) for p in items], total=total, page=page, page_size=page_size
    )


@router.post("/payments/{payment_id}/resolve")
def resolve_payment(payment_id: int, data: ResolveRequest, billing: BillingServiceDep) -> AdminPaymentRead:
    return AdminPaymentRead.from_payment(billing.resolve(payment_id, data.outcome))


@router.post("/users/{user_id}/subscription")
def change_subscription(
    user_id: int, data: SubscriptionChange, users: UserServiceDep, subscriptions: SubscriptionServiceDep
) -> SubscriptionRead:
    users.get(user_id)
    if data.action == "grant":
        subscriptions.grant(user_id, PlanCode.PREMIUM, data.days)
        return SubscriptionRead.model_validate(subscriptions.summary(user_id))
    return SubscriptionRead.model_validate(subscriptions.revoke(user_id))
