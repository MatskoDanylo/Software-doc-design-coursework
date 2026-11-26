from datetime import datetime

from sqlalchemy import or_, select

from app.models import Subscription, SubscriptionStatus
from app.repositories.base import SqlAlchemyRepository


class SubscriptionRepository(SqlAlchemyRepository[Subscription]):
    model = Subscription

    def get_active(self, user_id: int, now: datetime) -> Subscription | None:
        return self.session.scalar(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE.value, SubscriptionStatus.CANCELLED.value]),
                or_(Subscription.expires_at.is_(None), Subscription.expires_at > now),
            )
            .order_by(Subscription.started_at.desc(), Subscription.id.desc())
            .limit(1)
        )
