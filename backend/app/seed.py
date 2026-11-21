from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.models import Plan, PlanCode, Role
from app.repositories.plans import PlanRepository
from app.repositories.users import UserRepository
from app.schemas.common import normalize_email
from app.services.users import UserService

PLANS: tuple[dict[str, Any], ...] = (
    {"code": PlanCode.FREE, "name": "Free", "price_month": Decimal("0.00"), "ads_enabled": True, "max_height": 720},
    {"code": PlanCode.PREMIUM, "name": "Premium", "price_month": Decimal("99.00"), "ads_enabled": False, "max_height": 1080},
)


def seed_plans(session: Session) -> None:
    repo = PlanRepository(session)
    for spec in PLANS:
        plan = repo.get_by_code(spec["code"])
        if plan is None:
            repo.add(Plan(**spec))
            continue
        for field, value in spec.items():
            setattr(plan, field, value)


def seed_admin(session: Session, email: str, password: str) -> None:
    users = UserRepository(session)
    admin = users.get_by_email(normalize_email(email))
    if admin is None:
        UserService(users).create(email, password, "Administrator", Role.ADMIN)
    elif admin.role != Role.ADMIN:
        admin.role = Role.ADMIN


def seed(session: Session) -> None:
    seed_plans(session)
    seed_admin(session, settings.admin_email, settings.admin_password)


def main() -> None:
    with SessionLocal() as session, session.begin():
        seed(session)
    print(f"Seed complete: plans {[p['code'].value for p in PLANS]}, admin {settings.admin_email}")


if __name__ == "__main__":
    main()
