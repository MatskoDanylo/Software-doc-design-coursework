from collections.abc import Sequence

from sqlalchemy import func, select, update

from app.models import Notification
from app.repositories.base import SqlAlchemyRepository


class NotificationRepository(SqlAlchemyRepository[Notification]):
    model = Notification

    def list_for_user(self, user_id: int, unread_only: bool, limit: int) -> Sequence[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.read.is_(False))
        return self.session.scalars(
            query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)
        ).all()

    def unread_count(self, user_id: int) -> int:
        return self.session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read.is_(False))
        ) or 0

    def get_for_user(self, notification_id: int, user_id: int) -> Notification | None:
        return self.session.scalar(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )

    def mark_all_read(self, user_id: int) -> int:
        result = self.session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read.is_(False))
            .values(read=True)
            .execution_options(synchronize_session="fetch")
        )
        return result.rowcount
