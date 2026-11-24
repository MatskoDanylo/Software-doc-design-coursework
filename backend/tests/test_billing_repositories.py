from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import Notification, NotificationKind, Payment, PaymentStatus, PlanCode
from app.repositories.notification_repository import NotificationRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.plans import PlanRepository
from tests.factories import make_user

T0 = datetime(2026, 11, 24, 10, 0, tzinfo=UTC)


@pytest.fixture
def session(seeded: None) -> Iterator[Session]:
    with SessionLocal() as session, session.begin():
        yield session


def add_payments(session: Session, user_id: int, statuses: list[PaymentStatus]) -> list[Payment]:
    premium = PlanRepository(session).get_by_code(PlanCode.PREMIUM)
    assert premium is not None
    payments = [
        Payment(user_id=user_id, plan_id=premium.id, amount=Decimal("99.00"), status=status,
                created_at=T0 + timedelta(minutes=i))
        for i, status in enumerate(statuses)
    ]
    session.add_all(payments)
    session.flush()
    return payments


def add_notifications(session: Session, user_id: int, count: int, read: bool = False) -> list[Notification]:
    items = [
        Notification(user_id=user_id, kind=NotificationKind.PAYMENT_PENDING, message=f"#{i}", read=read,
                     created_at=T0 + timedelta(minutes=i))
        for i in range(count)
    ]
    session.add_all(items)
    session.flush()
    return items


def test_plans_are_listed_by_price(session: Session) -> None:
    assert [p.code for p in PlanRepository(session).list_all()] == ["free", "premium"]


def test_user_payments_are_isolated_and_newest_first(session: Session) -> None:
    alice, bob = make_user(session, "alice@example.com"), make_user(session, "bob@example.com")
    first, second = add_payments(session, alice.id, [PaymentStatus.FAILED, PaymentStatus.SUCCESS])
    [foreign] = add_payments(session, bob.id, [PaymentStatus.CREATED])
    repo = PaymentRepository(session)

    assert [p.id for p in repo.list_for_user(alice.id)] == [second.id, first.id]
    assert repo.get_for_user_for_update(first.id, alice.id) is first
    assert repo.get_for_user_for_update(foreign.id, alice.id) is None
    assert repo.get_for_update(foreign.id) is foreign


def test_payment_page_filters_by_status_and_paginates(session: Session) -> None:
    user = make_user(session, "alice@example.com")
    statuses = [PaymentStatus.PENDING, PaymentStatus.SUCCESS, PaymentStatus.PENDING, PaymentStatus.PENDING]
    payments = add_payments(session, user.id, statuses)
    repo = PaymentRepository(session)

    items, total = repo.page(PaymentStatus.PENDING, page=1, page_size=2)
    assert total == 3
    assert [p.id for p in items] == [payments[3].id, payments[2].id]
    assert items[0].user.email == "alice@example.com"

    items, total = repo.page(PaymentStatus.PENDING, page=2, page_size=2)
    assert [p.id for p in items] == [payments[0].id]

    assert repo.page(None, page=1, page_size=10)[1] == 4


def test_notifications_listing_and_unread_count(session: Session) -> None:
    alice, bob = make_user(session, "alice@example.com"), make_user(session, "bob@example.com")
    read = add_notifications(session, alice.id, 1, read=True)
    unread = add_notifications(session, alice.id, 3)
    add_notifications(session, bob.id, 2)
    repo = NotificationRepository(session)

    assert [n.id for n in repo.list_for_user(alice.id, unread_only=False, limit=2)] == [unread[2].id, unread[1].id]
    assert {n.id for n in repo.list_for_user(alice.id, unread_only=True, limit=10)} == {n.id for n in unread}
    assert repo.unread_count(alice.id) == 3
    assert repo.get_for_user(read[0].id, alice.id) is read[0]
    assert repo.get_for_user(read[0].id, bob.id) is None


def test_mark_all_read_touches_only_own_unread(session: Session) -> None:
    alice, bob = make_user(session, "alice@example.com"), make_user(session, "bob@example.com")
    add_notifications(session, alice.id, 1, read=True)
    mine = add_notifications(session, alice.id, 2)
    add_notifications(session, bob.id, 2)
    repo = NotificationRepository(session)

    assert repo.mark_all_read(alice.id) == 2
    assert all(n.read for n in mine)
    assert repo.unread_count(alice.id) == 0
    assert repo.unread_count(bob.id) == 2
