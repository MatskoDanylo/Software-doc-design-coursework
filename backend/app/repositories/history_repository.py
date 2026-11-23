from sqlalchemy import select

from app.models import WatchHistory
from app.repositories.base import SqlAlchemyRepository


class WatchHistoryRepository(SqlAlchemyRepository[WatchHistory]):
    model = WatchHistory

    def get_entry(self, user_id: int, title_id: int, episode_id: int | None) -> WatchHistory | None:
        return self.session.scalar(
            select(WatchHistory)
            .where(
                WatchHistory.user_id == user_id,
                WatchHistory.title_id == title_id,
                WatchHistory.episode_id.is_(None) if episode_id is None else WatchHistory.episode_id == episode_id,
            )
            .order_by(WatchHistory.last_watched.desc(), WatchHistory.id.desc())
            .limit(1)
        )
