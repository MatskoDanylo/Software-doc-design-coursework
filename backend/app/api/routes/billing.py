from fastapi import APIRouter, Depends, status

from app.api.deps import BillingServiceDep, CurrentUser, require_mock_payments
from app.schemas.billing import CheckoutRead, CheckoutRequest, MockResultRequest, PaymentRead

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", status_code=status.HTTP_201_CREATED)
def checkout(data: CheckoutRequest, user: CurrentUser, billing: BillingServiceDep) -> CheckoutRead:
    return CheckoutRead.from_checkout(billing.checkout(user, data.plan_code))


@router.post("/payments/{payment_id}/mock-result", dependencies=[Depends(require_mock_payments)])
def submit_mock_result(
    payment_id: int, data: MockResultRequest, user: CurrentUser, billing: BillingServiceDep
) -> PaymentRead:
    return PaymentRead.from_payment(billing.submit_mock_result(user, payment_id, data.outcome))


@router.get("/payments")
def payment_history(user: CurrentUser, billing: BillingServiceDep) -> list[PaymentRead]:
    return [PaymentRead.from_payment(payment) for payment in billing.history(user)]
