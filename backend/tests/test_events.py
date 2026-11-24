from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.events import (
    DomainEvent,
    EventBus,
    PaymentFailed,
    PaymentPending,
    PaymentSucceeded,
    SubscriptionActivated,
    WatchFinished,
)
from app.models import User
from tests.factories import make_user

SUCCEEDED = PaymentSucceeded(payment_id=1, user_id=7, plan_code="premium", amount=Decimal("99.00"))
FAILED = PaymentFailed(payment_id=2, user_id=7, plan_code="premium", amount=Decimal("99.00"))


class Recorder:
    def __init__(self, name: str, log: list[tuple[str, DomainEvent]]) -> None:
        self.name = name
        self.log = log

    def handle(self, event: DomainEvent, session: Session) -> None:
        self.log.append((self.name, event))


class Exploding:
    def handle(self, event: DomainEvent, session: Session) -> None:
        raise RuntimeError("handler failed")


class UserCreator:
    def __init__(self, email: str) -> None:
        self.email = email

    def handle(self, event: DomainEvent, session: Session) -> None:
        make_user(session, self.email)


class Republisher:
    def __init__(self, bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
        self.bus = bus
        self.log = log

    def handle(self, event: PaymentSucceeded, session: Session) -> None:
        self.log.append(("activator", event))
        self.bus.publish(SubscriptionActivated(user_id=event.user_id, subscription_id=1, plan_code="premium",
                                               expires_at=None))


class SelfRemoving:
    def __init__(self, bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
        self.bus = bus
        self.log = log

    def handle(self, event: PaymentSucceeded, session: Session) -> None:
        self.log.append(("once", event))
        self.bus.unsubscribe(PaymentSucceeded, self)


@pytest.fixture
def bus() -> EventBus:
    return EventBus(Session())


@pytest.fixture
def log() -> list[tuple[str, DomainEvent]]:
    return []


def test_subscribed_handler_receives_event_and_session(bus: EventBus) -> None:
    received: list[tuple[DomainEvent, Session]] = []

    class Spy:
        def handle(self, event: DomainEvent, session: Session) -> None:
            received.append((event, session))

    bus.subscribe(PaymentSucceeded, Spy())
    bus.publish(SUCCEEDED)

    assert received == [(SUCCEEDED, bus.session)]


def test_handlers_run_in_subscription_order(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    for name in ("first", "second", "third"):
        bus.subscribe(PaymentSucceeded, Recorder(name, log))

    bus.publish(SUCCEEDED)

    assert [name for name, _ in log] == ["first", "second", "third"]


def test_one_handler_can_observe_several_event_types(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    notifier = Recorder("notifier", log)
    bus.subscribe(PaymentSucceeded, notifier)
    bus.subscribe(PaymentFailed, notifier)

    bus.publish(SUCCEEDED)
    bus.publish(FAILED)

    assert log == [("notifier", SUCCEEDED), ("notifier", FAILED)]


def test_dispatch_is_by_exact_event_type(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    bus.subscribe(PaymentFailed, Recorder("failed", log))
    bus.subscribe(PaymentPending, Recorder("pending", log))

    bus.publish(SUCCEEDED)

    assert log == []


def test_unsubscribed_handler_is_not_called(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    kept, removed = Recorder("kept", log), Recorder("removed", log)
    bus.subscribe(PaymentSucceeded, kept)
    bus.subscribe(PaymentSucceeded, removed)

    bus.unsubscribe(PaymentSucceeded, removed)
    bus.publish(SUCCEEDED)

    assert log == [("kept", SUCCEEDED)]


def test_unsubscribe_of_unknown_handler_is_a_no_op(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    bus.unsubscribe(PaymentSucceeded, Recorder("ghost", log))

    assert bus.handlers_for(PaymentSucceeded) == ()


def test_subscribing_twice_does_not_duplicate_calls(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    handler = Recorder("once", log)
    bus.subscribe(PaymentSucceeded, handler)
    bus.subscribe(PaymentSucceeded, handler)

    bus.publish(SUCCEEDED)

    assert len(log) == 1


def test_handler_may_unsubscribe_itself_during_publish(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    bus.subscribe(PaymentSucceeded, SelfRemoving(bus, log))
    bus.subscribe(PaymentSucceeded, Recorder("after", log))

    bus.publish(SUCCEEDED)
    bus.publish(SUCCEEDED)

    assert [name for name, _ in log] == ["once", "after", "after"]


def test_nested_publish_is_handled_depth_first(bus: EventBus, log: list[tuple[str, DomainEvent]]) -> None:
    bus.subscribe(PaymentSucceeded, Republisher(bus, log))
    bus.subscribe(PaymentSucceeded, Recorder("audit", log))
    bus.subscribe(SubscriptionActivated, Recorder("notifier", log))

    bus.publish(SUCCEEDED)

    assert [name for name, _ in log] == ["activator", "notifier", "audit"]


def test_publish_without_subscribers_does_nothing(bus: EventBus) -> None:
    bus.publish(WatchFinished(user_id=1, title_id=2, episode_id=None))


def test_events_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        SUCCEEDED.amount = Decimal("0")  # type: ignore[misc]


def emails() -> list[str]:
    with SessionLocal() as session:
        return list(session.scalars(select(User.email).order_by(User.email)))


def test_handlers_share_the_publisher_transaction() -> None:
    with SessionLocal() as session, session.begin():
        bus = EventBus(session)
        bus.subscribe(PaymentSucceeded, UserCreator("observer@example.com"))
        make_user(session, "publisher@example.com")
        bus.publish(SUCCEEDED)

    assert emails() == ["observer@example.com", "publisher@example.com"]


def test_handler_error_rolls_back_the_whole_transaction() -> None:
    with pytest.raises(RuntimeError, match="handler failed"):
        with SessionLocal() as session, session.begin():
            bus = EventBus(session)
            bus.subscribe(PaymentSucceeded, UserCreator("observer@example.com"))
            bus.subscribe(PaymentSucceeded, Exploding())
            make_user(session, "publisher@example.com")
            bus.publish(SUCCEEDED)

    assert emails() == []
