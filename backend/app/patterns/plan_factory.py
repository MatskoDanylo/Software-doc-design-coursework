from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from app.core.errors import UnprocessableError
from app.models import Plan, PlanCode
from app.patterns.playback_proxy import PlaybackPolicy

CURRENCY = "UAH"


class UnknownPlanError(UnprocessableError):
    code = "unknown_plan"


@dataclass(frozen=True)
class PlanQuote:
    code: str
    name: str
    price: Decimal
    currency: str
    duration_days: int | None
    ads_enabled: bool
    max_height: int
    description: str
    purchasable: bool


class PlanPolicy(ABC):
    def __init__(self, plan: Plan) -> None:
        self.plan_code = plan.code
        self.name = plan.name
        self.max_height = plan.max_height

    @property
    @abstractmethod
    def ads_enabled(self) -> bool: ...

    @property
    @abstractmethod
    def price(self) -> Decimal: ...

    @property
    @abstractmethod
    def duration_days(self) -> int | None: ...

    @property
    def is_purchasable(self) -> bool:
        return self.price > 0

    @abstractmethod
    def describe(self) -> str: ...

    @abstractmethod
    def can_upgrade_to(self, other: "PlanPolicy") -> bool: ...


class FreePlanPolicy(PlanPolicy):
    @property
    def ads_enabled(self) -> bool:
        return True

    @property
    def price(self) -> Decimal:
        return Decimal("0.00")

    @property
    def duration_days(self) -> int | None:
        return None

    def describe(self) -> str:
        return f"Безкоштовно назавжди. Реклама перед відео, якість до {self.max_height}p."

    def can_upgrade_to(self, other: PlanPolicy) -> bool:
        return other.is_purchasable


class PremiumPlanPolicy(PlanPolicy):
    def __init__(self, plan: Plan, duration_days: int) -> None:
        super().__init__(plan)
        self._price = Decimal(plan.price_month).quantize(Decimal("0.01"))
        self._duration_days = duration_days

    @property
    def ads_enabled(self) -> bool:
        return False

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def duration_days(self) -> int | None:
        return self._duration_days

    def describe(self) -> str:
        return f"{self.price} грн за {self._duration_days} днів. Без реклами, якість до {self.max_height}p."

    def can_upgrade_to(self, other: PlanPolicy) -> bool:
        return False


class PlanPolicyCreator(ABC):
    plan_code: ClassVar[str]

    @abstractmethod
    def create_policy(self, plan: Plan) -> PlanPolicy: ...

    def build_playback_policy(self, plan: Plan) -> PlaybackPolicy:
        policy = self._policy(plan)
        return PlaybackPolicy(plan_code=policy.plan_code, max_height=policy.max_height, ads_enabled=policy.ads_enabled)

    def quote(self, plan: Plan) -> PlanQuote:
        policy = self._policy(plan)
        return PlanQuote(
            code=policy.plan_code,
            name=policy.name,
            price=policy.price,
            currency=CURRENCY,
            duration_days=policy.duration_days,
            ads_enabled=policy.ads_enabled,
            max_height=policy.max_height,
            description=policy.describe(),
            purchasable=policy.is_purchasable,
        )

    def _policy(self, plan: Plan) -> PlanPolicy:
        if plan.code != self.plan_code:
            raise ValueError(f"{type(self).__name__} cannot build a policy for plan '{plan.code}'")
        return self.create_policy(plan)


class FreePlanCreator(PlanPolicyCreator):
    plan_code = PlanCode.FREE

    def create_policy(self, plan: Plan) -> PlanPolicy:
        return FreePlanPolicy(plan)


class PremiumPlanCreator(PlanPolicyCreator):
    plan_code = PlanCode.PREMIUM

    def __init__(self, duration_days: int) -> None:
        if duration_days < 1:
            raise ValueError("Premium must last at least one day")
        self.duration_days = duration_days

    def create_policy(self, plan: Plan) -> PlanPolicy:
        return PremiumPlanPolicy(plan, self.duration_days)


class PlanPolicyRegistry:
    def __init__(self, creators: Iterable[PlanPolicyCreator]) -> None:
        self._creators = {str(creator.plan_code): creator for creator in creators}

    def creator_for(self, code: str) -> PlanPolicyCreator:
        creator = self._creators.get(code)
        if creator is None:
            raise UnknownPlanError(f"Plan '{code}' is not supported")
        return creator


def default_plan_registry(premium_days: int) -> PlanPolicyRegistry:
    return PlanPolicyRegistry([FreePlanCreator(), PremiumPlanCreator(premium_days)])
