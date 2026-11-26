from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.models import Payment, PaymentStatus
from app.repositories.base import SqlAlchemyRepository


class PaymentRepository(SqlAlchemyRepository[Payment]):
    model = Payment

    def get_for_update(self, payment_id: int) -> Payment | None:
        return self.session.scalar(self._locked().where(Payment.id == payment_id))

    def get_for_user_for_update(self, payment_id: int, user_id: int) -> Payment | None:
        return self.session.scalar(self._locked().where(Payment.id == payment_id, Payment.user_id == user_id))

    def list_for_user(self, user_id: int) -> Sequence[Payment]:
        return self.session.scalars(
            select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc(), Payment.id.desc())
        ).all()

    def page(self, status: PaymentStatus | None, page: int, page_size: int) -> tuple[Sequence[Payment], int]:
        conditions = [] if status is None else [Payment.status == status.value]
        total = self.session.scalar(select(func.count()).select_from(Payment).where(*conditions))
        items = self.session.scalars(
            select(Payment)
            .where(*conditions)
            .options(selectinload(Payment.user))
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
        return items, total or 0

    @staticmethod
    def _locked() -> Select[tuple[Payment]]:
        return select(Payment).with_for_update(of=Payment)
