from collections.abc import Sequence

from sqlalchemy import select

from app.models import Plan
from app.repositories.base import SqlAlchemyRepository


class PlanRepository(SqlAlchemyRepository[Plan]):
    model = Plan

    def get_by_code(self, code: str) -> Plan | None:
        return self.session.scalar(select(Plan).where(Plan.code == code))

    def list_all(self) -> Sequence[Plan]:
        return self.session.scalars(select(Plan).order_by(Plan.price_month, Plan.id)).all()
