from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import Payment, PaymentStatus
from app.patterns.payment_gateway import PaymentOutcome
from app.patterns.plan_factory import CURRENCY, PlanQuote
from app.services.billing_service import Checkout


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    price: Decimal
    currency: str
    duration_days: int | None
    ads_enabled: bool
    max_height: int
    description: str
    purchasable: bool

    @classmethod
    def from_quote(cls, quote: PlanQuote) -> "PlanRead":
        return cls.model_validate(quote)


class CheckoutRequest(BaseModel):
    plan_code: str = Field(min_length=1, max_length=30)


class CheckoutRead(BaseModel):
    payment_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    plan: PlanRead

    @classmethod
    def from_checkout(cls, checkout: Checkout) -> "CheckoutRead":
        return cls(
            payment_id=checkout.payment.id,
            amount=checkout.payment.amount,
            currency=checkout.quote.currency,
            status=PaymentStatus(checkout.payment.status),
            plan=PlanRead.from_quote(checkout.quote),
        )


class MockResultRequest(BaseModel):
    outcome: PaymentOutcome


class ResolveRequest(BaseModel):
    outcome: Literal[PaymentOutcome.SUCCESS, PaymentOutcome.FAILED]


class PaymentRead(BaseModel):
    id: int
    plan_code: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime
    paid_at: datetime | None

    @classmethod
    def from_payment(cls, payment: Payment) -> "PaymentRead":
        return cls(
            id=payment.id,
            plan_code=payment.plan.code,
            amount=payment.amount,
            currency=CURRENCY,
            status=PaymentStatus(payment.status),
            created_at=payment.created_at,
            paid_at=payment.paid_at,
        )


class AdminPaymentRead(PaymentRead):
    user_id: int
    user_email: str

    @classmethod
    def from_payment(cls, payment: Payment) -> "AdminPaymentRead":
        base = PaymentRead.from_payment(payment)
        return cls(**base.model_dump(), user_id=payment.user_id, user_email=payment.user.email)


class AdminPaymentPage(BaseModel):
    items: list[AdminPaymentRead]
    total: int
    page: int
    page_size: int


class SubscriptionChange(BaseModel):
    action: Literal["grant", "revoke"]
    days: int | None = Field(default=None, ge=1, le=3650)
