from datetime import datetime
from decimal import Decimal

import pytest

from app.models import Plan, PlanCode, Subscription
from app.patterns.plan_factory import (
    FreePlanCreator,
    FreePlanPolicy,
    PlanPolicyCreator,
    PlanQuote,
    PremiumPlanCreator,
    PremiumPlanPolicy,
    UnknownPlanError,
    default_plan_registry,
)
from app.patterns.playback_proxy import PlaybackPolicy, PlaybackProxy
from app.services.subscription_service import SubscriptionService
from tests.test_playback_proxy import AD_URL, FREE, PREMIUM, VIEWER, FakeRealPlayback, FixedAds, proxy

FREE_PLAN = Plan(id=1, code="free", name="Free", price_month=Decimal("0.00"), ads_enabled=True, max_height=720)
PREMIUM_PLAN = Plan(id=2, code="premium", name="Premium", price_month=Decimal("99.00"), ads_enabled=False,
                    max_height=1080)


class FakePlans:
    def get_by_code(self, code: str) -> Plan | None:
        return {"free": FREE_PLAN, "premium": PREMIUM_PLAN}.get(code)


class FakeSubscriptions:
    def __init__(self, plan: Plan | None) -> None:
        self.plan = plan

    def get_active(self, user_id: int, now: datetime) -> Subscription | None:
        return None if self.plan is None else Subscription(user_id=user_id, plan=self.plan)


def subscription_service(active_plan: Plan | None) -> SubscriptionService:
    return SubscriptionService(
        FakeSubscriptions(active_plan),
        FakePlans(),
        default_plan_registry(30),
    )


def test_free_creator_builds_free_policy_from_plan_row() -> None:
    policy = FreePlanCreator().create_policy(FREE_PLAN)

    assert isinstance(policy, FreePlanPolicy)
    assert (policy.plan_code, policy.name, policy.max_height) == ("free", "Free", 720)
    assert (policy.ads_enabled, policy.price, policy.duration_days, policy.is_purchasable) == (
        True, Decimal("0.00"), None, False,
    )


def test_premium_creator_builds_premium_policy_with_configured_duration() -> None:
    policy = PremiumPlanCreator(duration_days=45).create_policy(PREMIUM_PLAN)

    assert isinstance(policy, PremiumPlanPolicy)
    assert (policy.plan_code, policy.max_height, policy.price) == ("premium", 1080, Decimal("99.00"))
    assert (policy.ads_enabled, policy.duration_days, policy.is_purchasable) == (False, 45, True)


def test_tunable_values_come_from_the_database_row() -> None:
    plan = Plan(code="premium", name="Premium HD", price_month=Decimal("149.5"), ads_enabled=True, max_height=1440)

    policy = PremiumPlanCreator(30).create_policy(plan)

    assert (policy.name, policy.price, policy.max_height) == ("Premium HD", Decimal("149.50"), 1440)
    assert policy.ads_enabled is False


def test_plan_kind_rules_are_fixed_by_the_policy_class() -> None:
    misconfigured = Plan(code="free", name="Free", price_month=Decimal("10.00"), ads_enabled=False, max_height=720)

    policy = FreePlanCreator().create_policy(misconfigured)

    assert (policy.ads_enabled, policy.price, policy.is_purchasable) == (True, Decimal("0.00"), False)


def test_premium_creator_rejects_non_positive_duration() -> None:
    with pytest.raises(ValueError):
        PremiumPlanCreator(0)


@pytest.mark.parametrize(
    ("creator", "plan", "expected"),
    [(FreePlanCreator(), FREE_PLAN, FREE), (PremiumPlanCreator(30), PREMIUM_PLAN, PREMIUM)],
)
def test_build_playback_policy_uses_the_factory_method(
    creator: PlanPolicyCreator, plan: Plan, expected: PlaybackPolicy
) -> None:
    assert creator.build_playback_policy(plan) == expected


def test_quote_describes_premium_plan() -> None:
    assert PremiumPlanCreator(30).quote(PREMIUM_PLAN) == PlanQuote(
        code="premium",
        name="Premium",
        price=Decimal("99.00"),
        currency="UAH",
        duration_days=30,
        ads_enabled=False,
        max_height=1080,
        description="99.00 грн за 30 днів. Без реклами, якість до 1080p.",
        purchasable=True,
    )


def test_quote_describes_free_plan() -> None:
    quote = FreePlanCreator().quote(FREE_PLAN)

    assert (quote.price, quote.purchasable, quote.duration_days) == (Decimal("0.00"), False, None)
    assert quote.description == "Безкоштовно назавжди. Реклама перед відео, якість до 720p."


@pytest.mark.parametrize("creator", [FreePlanCreator(), PremiumPlanCreator(30)])
def test_creator_refuses_a_plan_of_another_kind(creator: PlanPolicyCreator) -> None:
    other = PREMIUM_PLAN if creator.plan_code == PlanCode.FREE else FREE_PLAN

    with pytest.raises(ValueError, match="cannot build a policy"):
        creator.quote(other)
    with pytest.raises(ValueError, match="cannot build a policy"):
        creator.build_playback_policy(other)


def test_upgrade_rules() -> None:
    free = FreePlanCreator().create_policy(FREE_PLAN)
    premium = PremiumPlanCreator(30).create_policy(PREMIUM_PLAN)

    assert free.can_upgrade_to(premium) is True
    assert free.can_upgrade_to(free) is False
    assert premium.can_upgrade_to(free) is False
    assert premium.can_upgrade_to(premium) is False


def test_registry_selects_creator_by_plan_code() -> None:
    registry = default_plan_registry(30)

    assert isinstance(registry.creator_for("free"), FreePlanCreator)
    assert isinstance(registry.creator_for(PlanCode.PREMIUM), PremiumPlanCreator)


def test_registry_rejects_unknown_plan_code() -> None:
    with pytest.raises(UnknownPlanError, match="'family'") as exc:
        default_plan_registry(30).creator_for("family")

    assert (exc.value.status_code, exc.value.code) == (422, "unknown_plan")


@pytest.mark.parametrize(("active_plan", "fixed"), [(None, FREE), (PREMIUM_PLAN, PREMIUM)])
def test_proxy_with_factory_backed_policies_behaves_as_before(
    active_plan: Plan | None, fixed: PlaybackPolicy
) -> None:
    service = subscription_service(active_plan)
    reference, _ = proxy(fixed)
    factory_backed = PlaybackProxy(FakeRealPlayback(), service, FixedAds(AD_URL))

    assert service.policy_for(VIEWER) == fixed
    assert factory_backed.get_playback(VIEWER, 1, None) == reference.get_playback(VIEWER, 1, None)
    assert factory_backed.get_master_manifest(VIEWER, 7) == reference.get_master_manifest(VIEWER, 7)
