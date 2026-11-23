from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.core.errors import NotFoundError, UnprocessableError
from app.models import Plan, PlanCode, Subscription, SubscriptionStatus, User
from app.patterns.playback_proxy import PlaybackPolicy
from app.services.ports import PlanStore, SubscriptionStore


def utc_now() -> datetime:
    return datetime.now(UTC)


class SubscriptionService:
    def __init__(
        self, subscriptions: SubscriptionStore, plans: PlanStore, clock: Callable[[], datetime] = utc_now
    ) -> None:
        self.subscriptions = subscriptions
        self.plans = plans
        self.clock = clock

    def current_plan(self, user: User) -> Plan:
        active = self.subscriptions.get_active(user.id, self.clock())
        return active.plan if active is not None else self._plan(PlanCode.FREE)

    def policy_for(self, user: User) -> PlaybackPolicy:
        plan = self.current_plan(user)
        return PlaybackPolicy(plan_code=plan.code, max_height=plan.max_height, ads_enabled=plan.ads_enabled)

    def grant(self, user: User, plan_code: PlanCode, days: int) -> Subscription:
        if days < 1:
            raise UnprocessableError("Subscription must last at least one day", code="invalid_duration")
        plan = self._plan(plan_code)
        now = self.clock()
        active = self.subscriptions.get_active(user.id, now)
        if active is not None and active.plan_id == plan.id:
            if active.expires_at is not None:
                active.expires_at = max(active.expires_at, now) + timedelta(days=days)
            return active
        if active is not None:
            active.status = SubscriptionStatus.CANCELLED
        return self.subscriptions.add(Subscription(
            user_id=user.id,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expires_at=now + timedelta(days=days),
        ))

    def _plan(self, code: PlanCode) -> Plan:
        plan = self.plans.get_by_code(code)
        if plan is None:
            raise NotFoundError(f"Plan '{code}' is not seeded; run `python -m app.seed`", code="plan_not_found")
        return plan
