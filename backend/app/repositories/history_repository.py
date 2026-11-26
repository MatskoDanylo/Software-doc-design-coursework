from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import distinct_on, insert
from sqlalchemy.orm import joinedload

from app.models import Episode, Title, WatchHistory
from app.repositories.base import SqlAlchemyRepository

UNIQUE_PROGRESS = "uq_watch_history_user_id"


class WatchHistoryRepository(SqlAlchemyRepository[WatchHistory]):
    model = WatchHistory

    def get_entry(self, user_id: int, title_id: int, episode_id: int | None) -> WatchHistory | None:
        return self.session.scalar(
            select(WatchHistory).where(
                WatchHistory.user_id == user_id,
                WatchHistory.title_id == title_id,
                WatchHistory.episode_id.is_not_distinct_from(episode_id),
            )
        )

    def upsert(
        self, user_id: int, title_id: int, episode_id: int | None, progress_sec: int, finished: bool
    ) -> WatchHistory:
        changes = {"progress_sec": progress_sec, "finished": finished, "last_watched": func.now()}
        statement = (
            insert(WatchHistory)
            .values(user_id=user_id, title_id=title_id, episode_id=episode_id, **changes)
            .on_conflict_do_update(constraint=UNIQUE_PROGRESS, set_=changes)
            .returning(WatchHistory)
        )
        return self.session.scalars(statement, execution_options={"populate_existing": True}).one()

    def continue_watching(self, user_id: int, limit: int) -> Sequence[WatchHistory]:
        latest_per_title = (
            select(WatchHistory.id)
            .where(WatchHistory.user_id == user_id, WatchHistory.finished.is_(False), WatchHistory.progress_sec > 0)
            .ext(distinct_on(WatchHistory.title_id))
            .order_by(WatchHistory.title_id, WatchHistory.last_watched.desc(), WatchHistory.id.desc())
        )
        return self.session.scalars(
            select(WatchHistory)
            .where(WatchHistory.id.in_(latest_per_title))
            .options(
                joinedload(WatchHistory.title).joinedload(Title.video),
                joinedload(WatchHistory.episode).joinedload(Episode.season),
                joinedload(WatchHistory.episode).joinedload(Episode.video),
            )
            .order_by(WatchHistory.last_watched.desc(), WatchHistory.id.desc())
            .limit(limit)
        ).all()
