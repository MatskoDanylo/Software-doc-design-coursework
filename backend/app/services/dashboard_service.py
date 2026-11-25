from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.services.reports import money


@dataclass(frozen=True)
class DashboardKpis:
    total_users: int
    active_users_7d: int
    active_premium: int
    revenue_30d: float
    titles_with_video: int


class DashboardSource(Protocol):
    def total_users(self) -> int: ...

    def active_users_since(self, days: int) -> int: ...

    def active_premium(self) -> int: ...

    def revenue_since(self, days: int) -> Decimal: ...

    def titles_with_video(self) -> int: ...


class DashboardService:
    ACTIVE_DAYS = 7
    REVENUE_DAYS = 30

    def __init__(self, source: DashboardSource) -> None:
        self.source = source

    def kpis(self) -> DashboardKpis:
        return DashboardKpis(
            total_users=self.source.total_users(),
            active_users_7d=self.source.active_users_since(self.ACTIVE_DAYS),
            active_premium=self.source.active_premium(),
            revenue_30d=money(self.source.revenue_since(self.REVENUE_DAYS)),
            titles_with_video=self.source.titles_with_video(),
        )
