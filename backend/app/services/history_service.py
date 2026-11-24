from collections.abc import Sequence
from dataclasses import dataclass

from app.core.events import EventPublisher, WatchFinished
from app.models import User, VideoStatus, WatchHistory
from app.schemas.history import HistoryEntryRead, ProgressUpdate
from app.services.favorite_service import mark_favorites
from app.services.playback_target import PlaybackTargetResolver
from app.services.ports import FavoriteReader, WatchHistoryStore


@dataclass(frozen=True)
class ProgressResult:
    entry: HistoryEntryRead
    just_finished: bool


class HistoryService:
    def __init__(
        self,
        history: WatchHistoryStore,
        targets: PlaybackTargetResolver,
        favorites: FavoriteReader,
        events: EventPublisher,
    ) -> None:
        self.history = history
        self.targets = targets
        self.favorites = favorites
        self.events = events

    def record_progress(self, user: User, data: ProgressUpdate) -> ProgressResult:
        target = self.targets.resolve(data.title_id, data.episode_id)
        previous = self.history.get_entry(user.id, target.title.id, target.episode_id)
        was_finished = previous is not None and previous.finished
        entry = self.history.upsert(user.id, target.title.id, target.episode_id, data.progress_sec, data.finished)
        just_finished = data.finished and not was_finished
        if just_finished:
            self.events.publish(WatchFinished(user_id=user.id, title_id=target.title.id, episode_id=target.episode_id))
        return ProgressResult(entry=self._read(user, [entry])[0], just_finished=just_finished)

    def continue_watching(self, user: User, limit: int) -> list[HistoryEntryRead]:
        return self._read(user, self.history.continue_watching(user.id, limit))

    def _read(self, user: User, entries: Sequence[WatchHistory]) -> list[HistoryEntryRead]:
        items = [HistoryEntryRead.model_validate(e) for e in entries]
        titles = mark_favorites([i.title for i in items], self.favorites, user.id)
        return [
            item.model_copy(update={"title": title, "duration_sec": _ready_duration(entry)})
            for item, title, entry in zip(items, titles, entries, strict=True)
        ]


def _ready_duration(entry: WatchHistory) -> int | None:
    video = entry.episode.video if entry.episode is not None else entry.title.video
    return video.duration_sec if video is not None and video.status == VideoStatus.READY else None
