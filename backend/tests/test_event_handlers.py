from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.events import (
    EventBus,
    PaymentFailed,
    PaymentPending,
    PaymentSucceeded,
    SubscriptionActivated,
    WatchFinished,
)
from app.event_wiring import create_event_bus
from app.models import Notification, NotificationKind, Subscription
from app.patterns.plan_factory import default_plan_registry
from app.services.notification_service import NotificationService, render
from app.services.subscription_activator import SubscriptionActivator
from app.services.subscription_service import SubscriptionService
from app.services.title_stats import TitleStatsUpdater

AMOUNT = Decimal("99.00")


class FakeGranter:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str, int | None]] = []

    def grant(self, user_id: int, plan_code: str, days: int | None = None) -> Subscription:
        self.calls.append((user_id, plan_code, days))
        return Subscription(id=1, user_id=user_id)


class FakeNotifications:
    def __init__(self) -> None:
        self.items: list[Notification] = []

    def add(self, entity: Notification) -> Notification:
        self.items.append(entity)
        return entity


def test_activator_grants_plan_duration_for_the_paid_plan() -> None:
    granter = FakeGranter()
    sessions: list[Session] = []

    def factory(session: Session) -> FakeGranter:
        sessions.append(session)
        return granter

    session = Session()
    SubscriptionActivator(factory).handle(PaymentSucceeded(1, 7, "premium", AMOUNT), session)

    assert granter.calls == [(7, "premium", None)]
    assert sessions == [session]


@pytest.mark.parametrize(
    ("event", "kind", "message"),
    [
        (
            PaymentPending(1, 7, "premium", AMOUNT),
            NotificationKind.PAYMENT_PENDING,
            "Оплата 99.00 грн за Преміум очікує підтвердження банку.",
        ),
        (
            PaymentFailed(1, 7, "premium", AMOUNT),
            NotificationKind.PAYMENT_FAILED,
            "Оплату 99.00 грн за Преміум відхилено. Спробуйте ще раз.",
        ),
        (
            SubscriptionActivated(7, 3, "premium", datetime(2026, 12, 24, 9, 30, tzinfo=UTC)),
            NotificationKind.SUBSCRIPTION_ACTIVATED,
            "Підписку Преміум активовано до 24.12.2026.",
        ),
        (
            SubscriptionActivated(7, 3, "premium", None),
            NotificationKind.SUBSCRIPTION_ACTIVATED,
            "Підписку Преміум активовано.",
        ),
    ],
)
def test_notification_messages(
    event: PaymentPending | PaymentFailed | SubscriptionActivated, kind: NotificationKind, message: str
) -> None:
    assert render(event) == (kind, message)


def test_notification_service_stores_message_for_event_owner() -> None:
    store = FakeNotifications()

    NotificationService(lambda session: store).handle(PaymentFailed(1, 7, "premium", AMOUNT), Session())

    [item] = store.items
    assert (item.user_id, item.kind) == (7, NotificationKind.PAYMENT_FAILED)


def test_wiring_subscribes_observers_to_domain_events() -> None:
    bus = create_event_bus(Session(), default_plan_registry(30))

    def handler_types(event_type: type) -> list[type]:
        return [type(h) for h in bus.handlers_for(event_type)]

    assert handler_types(PaymentSucceeded) == [SubscriptionActivator]
    assert handler_types(PaymentPending) == [NotificationService]
    assert handler_types(PaymentFailed) == [NotificationService]
    assert handler_types(SubscriptionActivated) == [NotificationService]
    assert handler_types(WatchFinished) == [TitleStatsUpdater]


def test_wired_activator_publishes_back_into_the_same_bus() -> None:
    bus = create_event_bus(Session(), default_plan_registry(30))
    [activator] = bus.handlers_for(PaymentSucceeded)

    assert isinstance(activator, SubscriptionActivator)
    service = activator.subscriptions(bus.session)
    assert isinstance(service, SubscriptionService)
    assert service.events is bus
    assert isinstance(bus, EventBus)
