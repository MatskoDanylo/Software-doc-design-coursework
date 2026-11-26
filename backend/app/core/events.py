from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from sqlalchemy.orm import Session


@dataclass(frozen=True)
class DomainEvent:
    pass


@dataclass(frozen=True)
class PaymentSucceeded(DomainEvent):
    payment_id: int
    user_id: int
    plan_code: str
    amount: Decimal


@dataclass(frozen=True)
class PaymentPending(DomainEvent):
    payment_id: int
    user_id: int
    plan_code: str
    amount: Decimal


@dataclass(frozen=True)
class PaymentFailed(DomainEvent):
    payment_id: int
    user_id: int
    plan_code: str
    amount: Decimal


@dataclass(frozen=True)
class SubscriptionActivated(DomainEvent):
    user_id: int
    subscription_id: int
    plan_code: str
    expires_at: datetime | None


@dataclass(frozen=True)
class WatchFinished(DomainEvent):
    user_id: int
    title_id: int
    episode_id: int | None


class EventHandler[E: DomainEvent](Protocol):
    def handle(self, event: E, session: Session) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


class EventBus:
    """Synchronous in-process Subject bound to one unit of work.

    Handlers run in the caller's transaction and must not commit; an exception from a handler
    propagates to the caller, so the whole transaction is rolled back.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._handlers: dict[type[DomainEvent], list[EventHandler[Any]]] = {}

    def subscribe[E: DomainEvent](self, event_type: type[E], handler: EventHandler[E]) -> None:
        handlers = self._handlers.setdefault(event_type, [])
        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe[E: DomainEvent](self, event_type: type[E], handler: EventHandler[E]) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def handlers_for(self, event_type: type[DomainEvent]) -> tuple[EventHandler[Any], ...]:
        return tuple(self._handlers.get(event_type, ()))

    def publish(self, event: DomainEvent) -> None:
        for handler in self.handlers_for(type(event)):
            handler.handle(event, self.session)
