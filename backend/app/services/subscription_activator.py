from collections.abc import Callable
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.events import PaymentSucceeded
from app.models import Subscription


class SubscriptionGranter(Protocol):
    def grant(self, user_id: int, plan_code: str, days: int | None = None) -> Subscription: ...


class SubscriptionActivator:
    def __init__(self, subscriptions: Callable[[Session], SubscriptionGranter]) -> None:
        self.subscriptions = subscriptions

    def handle(self, event: PaymentSucceeded, session: Session) -> None:
        self.subscriptions(session).grant(event.user_id, event.plan_code)
