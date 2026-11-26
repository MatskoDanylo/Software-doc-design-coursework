from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import TitleStats, TitleViewer, WatchHistory
from app.services.ports import StatsTotals


class TitleStatsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, title_id: int) -> TitleStats | None:
        return self.session.get(TitleStats, title_id, populate_existing=True)

    def record_completion(self, title_id: int, user_id: int) -> bool:
        viewer = (
            insert(TitleViewer)
            .values(title_id=title_id, user_id=user_id)
            .on_conflict_do_nothing()
            .returning(TitleViewer.user_id)
        )
        new_viewer = self.session.scalar(viewer) is not None
        added = int(new_viewer)
        stats = insert(TitleStats).values(
            title_id=title_id, unique_viewers=added, completions=1, last_watched_at=func.now()
        )
        self.session.execute(
            stats.on_conflict_do_update(
                index_elements=[TitleStats.title_id],
                set_={
                    "unique_viewers": TitleStats.unique_viewers + added,
                    "completions": TitleStats.completions + 1,
                    "last_watched_at": func.now(),
                },
            )
        )
        return new_viewer

    def rebuild(self) -> StatsTotals:
        self.session.execute(delete(TitleViewer))
        self.session.execute(delete(TitleStats))
        finished = WatchHistory.finished.is_(True)
        self.session.execute(
            insert(TitleViewer).from_select(
                ["title_id", "user_id", "first_finished_at"],
                select(WatchHistory.title_id, WatchHistory.user_id, func.min(WatchHistory.last_watched))
                .where(finished)
                .group_by(WatchHistory.title_id, WatchHistory.user_id),
            )
        )
        self.session.execute(
            insert(TitleStats).from_select(
                ["title_id", "unique_viewers", "completions", "last_watched_at"],
                select(
                    WatchHistory.title_id,
                    func.count(WatchHistory.user_id.distinct()),
                    func.count(),
                    func.max(WatchHistory.last_watched),
                )
                .where(finished)
                .group_by(WatchHistory.title_id),
            )
        )
        titles, viewers, completions = self.session.execute(
            select(
                func.count(),
                func.coalesce(func.sum(TitleStats.unique_viewers), 0),
                func.coalesce(func.sum(TitleStats.completions), 0),
            )
        ).one()
        return StatsTotals(titles=titles, viewers=viewers, completions=completions)
