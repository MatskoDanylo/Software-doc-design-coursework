from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.events import PaymentFailed, PaymentPending, SubscriptionActivated
from app.models import Notification, NotificationKind, PlanCode
from app.services.ports import NotificationStore

type NotifiableEvent = PaymentPending | PaymentFailed | SubscriptionActivated

PLAN_LABELS: dict[str, str] = {PlanCode.FREE: "Безкоштовний", PlanCode.PREMIUM: "Преміум"}


class NotificationService:
    def __init__(self, notifications: Callable[[Session], NotificationStore]) -> None:
        self.notifications = notifications

    def handle(self, event: NotifiableEvent, session: Session) -> None:
        kind, message = render(event)
        self.notifications(session).add(Notification(user_id=event.user_id, kind=kind, message=message))


def render(event: NotifiableEvent) -> tuple[NotificationKind, str]:
    plan = PLAN_LABELS.get(event.plan_code, event.plan_code)
    match event:
        case PaymentPending(amount=amount):
            return NotificationKind.PAYMENT_PENDING, f"Оплата {amount} грн за {plan} очікує підтвердження банку."
        case PaymentFailed(amount=amount):
            return NotificationKind.PAYMENT_FAILED, f"Оплату {amount} грн за {plan} відхилено. Спробуйте ще раз."
        case SubscriptionActivated(expires_at=None):
            return NotificationKind.SUBSCRIPTION_ACTIVATED, f"Підписку {plan} активовано."
        case SubscriptionActivated(expires_at=expires_at):
            return NotificationKind.SUBSCRIPTION_ACTIVATED, f"Підписку {plan} активовано до {expires_at:%d.%m.%Y}."
