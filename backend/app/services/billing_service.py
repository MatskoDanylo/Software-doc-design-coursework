from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.events import EventPublisher, PaymentFailed, PaymentPending, PaymentSucceeded
from app.models import Payment, PaymentStatus, Plan, User
from app.patterns.payment_gateway import GatewayPaymentNotFound, PaymentGateway, PaymentOutcome, PaymentSimulator
from app.patterns.plan_factory import CURRENCY, PlanPolicyRegistry, PlanQuote
from app.services.ports import PaymentStore, PlanStore
from app.services.subscription_service import utc_now

PAYMENT_EVENTS = {
    PaymentStatus.SUCCESS: PaymentSucceeded,
    PaymentStatus.PENDING: PaymentPending,
    PaymentStatus.FAILED: PaymentFailed,
}


class CurrentPlanReader(Protocol):
    def current_plan(self, user: User) -> Plan: ...


@dataclass(frozen=True)
class Checkout:
    payment: Payment
    quote: PlanQuote


class BillingService:
    def __init__(
        self,
        payments: PaymentStore,
        plans: PlanStore,
        gateway: PaymentGateway,
        simulator: PaymentSimulator,
        plan_policies: PlanPolicyRegistry,
        current_plans: CurrentPlanReader,
        events: EventPublisher,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.payments = payments
        self.plans = plans
        self.gateway = gateway
        self.simulator = simulator
        self.plan_policies = plan_policies
        self.current_plans = current_plans
        self.events = events
        self.clock = clock

    def list_plans(self) -> list[PlanQuote]:
        return [self.plan_policies.creator_for(plan.code).quote(plan) for plan in self.plans.list_all()]

    def checkout(self, user: User, plan_code: str) -> Checkout:
        plan = self.plans.get_by_code(plan_code)
        if plan is None:
            raise NotFoundError(f"Plan '{plan_code}' does not exist", code="plan_not_found")
        creator = self.plan_policies.creator_for(plan.code)
        target = creator.create_policy(plan)
        if not target.is_purchasable:
            raise UnprocessableError(f"Plan '{plan.code}' cannot be purchased", code="plan_not_purchasable")
        current_plan = self.current_plans.current_plan(user)
        current = self.plan_policies.creator_for(current_plan.code).create_policy(current_plan)
        if current.plan_code != target.plan_code and not current.can_upgrade_to(target):
            raise ConflictError(
                f"Switching from '{current.plan_code}' to '{target.plan_code}' is not allowed",
                code="plan_change_not_allowed",
            )
        quote = creator.quote(plan)
        payment = self.payments.add(Payment(
            user_id=user.id, plan=plan, amount=quote.price, status=PaymentStatus.CREATED,
            provider=self.gateway.provider_name,
        ))
        self._open_invoice(payment)
        return Checkout(payment=payment, quote=quote)

    def submit_mock_result(self, user: User, payment_id: int, outcome: PaymentOutcome) -> Payment:
        payment = self.payments.get_for_user_for_update(payment_id, user.id)
        if payment is None:
            raise NotFoundError("Payment not found", code="payment_not_found")
        return self._settle(payment, outcome)

    def resolve(self, payment_id: int, outcome: PaymentOutcome) -> Payment:
        if outcome == PaymentOutcome.PENDING:
            raise UnprocessableError("A pending payment can only be resolved as success or failed",
                                     code="invalid_outcome")
        payment = self.payments.get_for_update(payment_id)
        if payment is None:
            raise NotFoundError("Payment not found", code="payment_not_found")
        if payment.status != PaymentStatus.PENDING:
            raise ConflictError(f"Payment is {payment.status}, not pending", code="payment_not_pending")
        return self._settle(payment, outcome)

    def history(self, user: User) -> Sequence[Payment]:
        return self.payments.list_for_user(user.id)

    def _settle(self, payment: Payment, outcome: PaymentOutcome) -> Payment:
        status = PaymentStatus(payment.status)
        if status == PaymentStatus.SUCCESS and outcome == PaymentOutcome.SUCCESS:
            return payment
        if status.is_final:
            raise ConflictError(f"Payment is already {status}", code="payment_finalized")
        return self._apply(payment, self._gateway_result(payment, outcome))

    def _gateway_result(self, payment: Payment, outcome: PaymentOutcome) -> PaymentStatus:
        external_id = payment.external_id
        known = self._known_status(external_id) if external_id is not None else None
        if known is not None and known.is_final:
            return known
        if external_id is None or known is None:
            external_id = self._open_invoice(payment)
        return self.simulator.simulate(external_id, outcome).status

    def _known_status(self, external_id: str) -> PaymentStatus | None:
        try:
            return self.gateway.get_status(external_id)
        except GatewayPaymentNotFound:
            return None

    def _open_invoice(self, payment: Payment) -> str:
        invoice = self.gateway.create_payment(payment.id, payment.amount, CURRENCY, f"Cinema {payment.plan.name}")
        payment.external_id = invoice.external_id
        self.payments.save(payment)
        return invoice.external_id

    def _apply(self, payment: Payment, status: PaymentStatus) -> Payment:
        event_type = PAYMENT_EVENTS.get(status)
        if status == payment.status or event_type is None:
            return payment
        payment.status = status
        if status == PaymentStatus.SUCCESS:
            payment.paid_at = self.clock()
        self.payments.save(payment)
        self.events.publish(event_type(
            payment_id=payment.id, user_id=payment.user_id, plan_code=payment.plan.code, amount=payment.amount
        ))
        return payment
