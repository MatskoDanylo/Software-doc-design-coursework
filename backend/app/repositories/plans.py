from sqlalchemy import select

from app.models import Plan
from app.repositories.base import SqlAlchemyRepository


class PlanRepository(SqlAlchemyRepository[Plan]):
    model = Plan

    def get_by_code(self, code: str) -> Plan | None:
        return self.session.scalar(select(Plan).where(Plan.code == code))
