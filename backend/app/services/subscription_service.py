from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.events import EventPublisher, SubscriptionActivated
from app.models import Plan, PlanCode, Subscription, SubscriptionStatus, User
from app.patterns.plan_factory import PlanPolicyRegistry
from app.patterns.playback_proxy import PlaybackPolicy
from app.services.ports import PlanStore, SubscriptionStore


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class SubscriptionInfo:
    plan_code: str
    expires_at: datetime | None
    cancelled: bool


FREE_INFO = SubscriptionInfo(plan_code=PlanCode.FREE, expires_at=None, cancelled=False)


class SubscriptionService:
    def __init__(
        self,
        subscriptions: SubscriptionStore,
        plans: PlanStore,
        plan_policies: PlanPolicyRegistry,
        events: EventPublisher,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.subscriptions = subscriptions
        self.plans = plans
        self.plan_policies = plan_policies
        self.events = events
        self.clock = clock

    def current_plan(self, user: User) -> Plan:
        active = self.subscriptions.get_active(user.id, self.clock())
        return active.plan if active is not None else self._plan(PlanCode.FREE)

    def policy_for(self, user: User) -> PlaybackPolicy:
        plan = self.current_plan(user)
        return self.plan_policies.creator_for(plan.code).build_playback_policy(plan)

    def summary(self, user_id: int) -> SubscriptionInfo:
        active = self.subscriptions.get_active(user_id, self.clock())
        return FREE_INFO if active is None else _info(active)

    def grant(self, user_id: int, plan_code: str, days: int | None = None) -> Subscription:
        if days is not None and days < 1:
            raise UnprocessableError("Subscription must last at least one day", code="invalid_duration")
        plan = self._plan(plan_code)
        duration = days if days is not None else self._default_duration(plan)
        now = self.clock()
        active = self.subscriptions.get_active(user_id, now)
        if active is not None and active.plan_id == plan.id:
            subscription = active
            subscription.status = SubscriptionStatus.ACTIVE
            if subscription.expires_at is not None:
                subscription.expires_at = max(subscription.expires_at, now) + timedelta(days=duration)
            self.subscriptions.save(subscription)
        else:
            if active is not None:
                active.status = SubscriptionStatus.EXPIRED
                self.subscriptions.save(active)
            subscription = self.subscriptions.add(
                Subscription(
                    user_id=user_id,
                    plan=plan,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=now,
                    expires_at=now + timedelta(days=duration),
                )
            )
        self.events.publish(
            SubscriptionActivated(
                user_id=user_id,
                subscription_id=subscription.id,
                plan_code=plan.code,
                expires_at=subscription.expires_at,
            )
        )
        return subscription

    def cancel(self, user: User) -> SubscriptionInfo:
        active = self.subscriptions.get_active(user.id, self.clock())
        if active is None:
            raise ConflictError("There is no active subscription to cancel", code="no_active_subscription")
        active.status = SubscriptionStatus.CANCELLED
        return _info(self.subscriptions.save(active))

    def revoke(self, user_id: int) -> SubscriptionInfo:
        now = self.clock()
        active = self.subscriptions.get_active(user_id, now)
        if active is not None:
            active.status = SubscriptionStatus.EXPIRED
            active.expires_at = now
            self.subscriptions.save(active)
        return FREE_INFO

    def _default_duration(self, plan: Plan) -> int:
        duration = self.plan_policies.creator_for(plan.code).create_policy(plan).duration_days
        if duration is None:
            raise UnprocessableError(f"Plan '{plan.code}' cannot be granted as a subscription", code="invalid_duration")
        return duration

    def _plan(self, code: str) -> Plan:
        plan = self.plans.get_by_code(code)
        if plan is None:
            raise NotFoundError(f"Plan '{code}' is not seeded; run `python -m app.seed`", code="plan_not_found")
        return plan


def _info(subscription: Subscription) -> SubscriptionInfo:
    return SubscriptionInfo(
        plan_code=subscription.plan.code,
        expires_at=subscription.expires_at,
        cancelled=subscription.status == SubscriptionStatus.CANCELLED,
    )
