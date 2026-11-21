from decimal import Decimal

from sqlalchemy import func, select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import verify_password
from app.models import Plan, PlanCode, Role, User
from app.seed import seed


def _run_seed() -> None:
    with SessionLocal() as session, session.begin():
        seed(session)


def test_seed_creates_plans_and_admin() -> None:
    _run_seed()

    with SessionLocal() as session:
        plans = {p.code: p for p in session.scalars(select(Plan))}
        admin = session.scalar(select(User).where(User.email == settings.admin_email))

    assert set(plans) == {PlanCode.FREE, PlanCode.PREMIUM}
    free, premium = plans[PlanCode.FREE], plans[PlanCode.PREMIUM]
    assert (free.ads_enabled, free.max_height, free.price_month) == (True, 720, Decimal("0.00"))
    assert (premium.ads_enabled, premium.max_height, premium.price_month) == (False, 1080, Decimal("99.00"))
    assert admin is not None and admin.role == Role.ADMIN and admin.profile is not None
    assert verify_password(settings.admin_password, admin.password_hash)


def test_seed_is_idempotent_and_restores_reference_values() -> None:
    _run_seed()
    with SessionLocal() as session, session.begin():
        session.scalar(select(Plan).where(Plan.code == PlanCode.PREMIUM)).price_month = Decimal("1.00")
        admin = session.scalar(select(User).where(User.email == settings.admin_email))
        admin.role = Role.USER
        original_hash = admin.password_hash

    _run_seed()

    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Plan)) == 2
        assert session.scalar(select(func.count()).select_from(User)) == 1
        premium = session.scalar(select(Plan).where(Plan.code == PlanCode.PREMIUM))
        admin = session.scalar(select(User).where(User.email == settings.admin_email))
    assert premium.price_month == Decimal("99.00")
    assert admin.role == Role.ADMIN
    assert admin.password_hash == original_hash
