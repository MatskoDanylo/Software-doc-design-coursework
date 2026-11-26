import argparse
from collections.abc import Sequence

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.errors import AppError
from app.event_wiring import create_event_bus
from app.models import PlanCode
from app.patterns.plan_factory import default_plan_registry
from app.repositories.plans import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.users import UserRepository
from app.schemas.common import normalize_email
from app.services.subscription_service import SubscriptionService


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.grant_premium", description="Activate or extend a Premium subscription."
    )
    parser.add_argument("email", help="email of an existing user")
    parser.add_argument("--days", type=int, help="subscription length in days (default: Premium plan duration)")
    args = parser.parse_args(argv)

    with SessionLocal() as session, session.begin():
        user = UserRepository(session).get_by_email(normalize_email(args.email))
        if user is None:
            print(f"User {args.email} not found")
            return 1
        plan_policies = default_plan_registry(settings.premium_days)
        service = SubscriptionService(
            SubscriptionRepository(session),
            PlanRepository(session),
            plan_policies,
            create_event_bus(session, plan_policies),
        )
        try:
            subscription = service.grant(user.id, PlanCode.PREMIUM, args.days)
        except AppError as exc:
            print(exc.message)
            return 1
        expires = subscription.expires_at.isoformat() if subscription.expires_at else "never"
        print(f"Premium active for {user.email} until {expires}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
