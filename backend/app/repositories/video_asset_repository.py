from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import select, update

from app.core.db import SessionLocal
from app.models import VideoAsset, VideoStatus
from app.repositories.base import SqlAlchemyRepository


class VideoAssetRepository(SqlAlchemyRepository[VideoAsset]):
    model = VideoAsset

    def get_by_title(self, title_id: int) -> VideoAsset | None:
        return self.session.scalar(select(VideoAsset).where(VideoAsset.title_id == title_id))

    def get_by_episode(self, episode_id: int) -> VideoAsset | None:
        return self.session.scalar(select(VideoAsset).where(VideoAsset.episode_id == episode_id))

    def fail_processing(self, message: str) -> int:
        result = self.session.execute(
            update(VideoAsset)
            .where(VideoAsset.status == VideoStatus.PROCESSING.value)
            .values(status=VideoStatus.FAILED.value, error_message=message)
        )
        return result.rowcount


@contextmanager
def video_asset_transaction() -> Iterator[VideoAssetRepository]:
    with SessionLocal() as session, session.begin():
        yield VideoAssetRepository(session)
