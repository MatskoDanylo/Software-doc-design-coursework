import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import PurePath
from typing import BinaryIO

from app.core.errors import ConflictError, NotFoundError, UnsupportedMediaTypeError
from app.core.storage import VideoFileStore
from app.models import Episode, Title, TitleKind, VideoAsset, VideoStatus
from app.schemas.video import VideoAssetRead
from app.services.hls_transcoder import TranscodeError, VideoTranscoder
from app.services.ports import EntityStore, VideoAssetStore

logger = logging.getLogger(__name__)

INTERRUPTED_MESSAGE = "interrupted by restart"
_ISO_BMFF_BOXES = {b"ftyp", b"moov", b"mdat", b"wide", b"free"}
_MATROSKA_MAGIC = b"\x1a\x45\xdf\xa3"


def detect_video_extension(filename: str | None, head: bytes) -> str | None:
    extension = PurePath(filename or "").suffix.lower().lstrip(".")
    if extension == "mp4" and head[4:8] == b"ftyp":
        return extension
    if extension == "mov" and head[4:8] in _ISO_BMFF_BOXES:
        return extension
    if extension == "mkv" and head.startswith(_MATROSKA_MAGIC):
        return extension
    return None


class VideoUploadService:
    def __init__(
        self,
        titles: EntityStore[Title],
        episodes: EntityStore[Episode],
        assets: VideoAssetStore,
        store: VideoFileStore,
        max_bytes: int,
    ) -> None:
        self.titles = titles
        self.episodes = episodes
        self.assets = assets
        self.store = store
        self.max_bytes = max_bytes

    def upload_for_title(self, title_id: int, stream: BinaryIO, filename: str | None) -> VideoAssetRead:
        extension = self._check_format(stream, filename)
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("Title not found", code="title_not_found")
        if title.kind != TitleKind.MOVIE:
            raise ConflictError("Series videos are uploaded per episode", code="not_a_movie")
        asset = self.assets.get_by_title(title.id) or self.assets.add(VideoAsset(title_id=title.id))
        return self._accept(asset, stream, extension)

    def upload_for_episode(self, episode_id: int, stream: BinaryIO, filename: str | None) -> VideoAssetRead:
        extension = self._check_format(stream, filename)
        episode = self.episodes.get(episode_id)
        if episode is None:
            raise NotFoundError("Episode not found", code="episode_not_found")
        asset = self.assets.get_by_episode(episode.id) or self.assets.add(VideoAsset(episode_id=episode.id))
        return self._accept(asset, stream, extension)

    def get_asset(self, asset_id: int) -> VideoAssetRead:
        asset = self.assets.get(asset_id)
        if asset is None:
            raise NotFoundError("Video asset not found", code="video_asset_not_found")
        return VideoAssetRead.model_validate(asset)

    @staticmethod
    def _check_format(stream: BinaryIO, filename: str | None) -> str:
        head = stream.read(16)
        stream.seek(0)
        extension = detect_video_extension(filename, head)
        if extension is None:
            raise UnsupportedMediaTypeError("Video must be an MP4, MKV or MOV file")
        return extension

    def _accept(self, asset: VideoAsset, stream: BinaryIO, extension: str) -> VideoAssetRead:
        if asset.status == VideoStatus.PROCESSING:
            raise ConflictError("Previous upload is still being processed", code="video_processing")
        self.store.save_source(asset.id, stream, extension, self.max_bytes)
        asset.status = VideoStatus.PENDING
        asset.error_message = None
        asset.hls_path = None
        return VideoAssetRead.model_validate(asset)


AssetTransaction = Callable[[], AbstractContextManager[VideoAssetStore]]


class VideoProcessingService:
    def __init__(self, transaction: AssetTransaction, transcoder: VideoTranscoder, store: VideoFileStore) -> None:
        self.transaction = transaction
        self.transcoder = transcoder
        self.store = store

    def process(self, asset_id: int) -> VideoStatus | None:
        with self.transaction() as assets:
            asset = assets.get(asset_id)
            if asset is None or asset.status != VideoStatus.PENDING:
                return None
            asset.status = VideoStatus.PROCESSING

        try:
            source = self.store.source_path(asset_id)
            if source is None:
                raise TranscodeError("Source file is missing")
            self.transcoder.transcode(source, self.store.hls_dir(asset_id))
        except Exception as exc:
            if not isinstance(exc, TranscodeError):
                logger.exception("Unexpected error while transcoding video asset %s", asset_id)
            return self._finish(asset_id, VideoStatus.FAILED, error_message=str(exc) or type(exc).__name__)

        self.store.remove_source(asset_id)
        return self._finish(asset_id, VideoStatus.READY, hls_path=self.store.master_path(asset_id))

    def fail_interrupted(self) -> int:
        with self.transaction() as assets:
            return assets.fail_processing(INTERRUPTED_MESSAGE)

    def _finish(
        self, asset_id: int, status: VideoStatus, error_message: str | None = None, hls_path: str | None = None
    ) -> VideoStatus | None:
        with self.transaction() as assets:
            asset = assets.get(asset_id)
            if asset is None:
                return None
            asset.status = status
            asset.error_message = error_message
            asset.hls_path = hls_path
            return status
