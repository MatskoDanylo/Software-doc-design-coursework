from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.events import WatchFinished
from app.services.ports import CompletionRecorder, StatsTotals, TitleStatsStore


class TitleStatsUpdater:
    def __init__(self, stats: Callable[[Session], CompletionRecorder]) -> None:
        self.stats = stats

    def handle(self, event: WatchFinished, session: Session) -> None:
        self.stats(session).record_completion(event.title_id, event.user_id)


class TitleStatsService:
    def __init__(self, stats: TitleStatsStore) -> None:
        self.stats = stats

    def rebuild(self) -> StatsTotals:
        return self.stats.rebuild()
