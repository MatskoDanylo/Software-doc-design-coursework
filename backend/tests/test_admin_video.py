import io
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_transcoder, get_video_upload_limit
from app.core.config import settings
from app.core.db import SessionLocal
from app.core.storage import LocalVideoStore
from app.main import app
from app.models import TitleKind, VideoAsset, VideoStatus
from app.repositories.video_asset_repository import video_asset_transaction
from app.services.hls_playlist import MasterPlaylist, Variant
from app.services.hls_transcoder import DEFAULT_RENDITIONS, Rendition, TranscodeError
from app.services.video_service import INTERRUPTED_MESSAGE, VideoProcessingService
from tests.factories import add_season, make_title
from tests.helpers import assert_error

MP4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 64
MKV = b"\x1a\x45\xdf\xa3" + b"\x00" * 64
MEDIA = Path(settings.media_dir)


class FakeTranscoder:
    def __init__(self) -> None:
        self.calls: list[Path] = []
        self.received: list[bytes] = []
        self.error: Exception | None = None

    def transcode(
        self, source: Path, output_dir: Path, renditions: Sequence[Rendition] = DEFAULT_RENDITIONS
    ) -> MasterPlaylist:
        self.calls.append(source)
        self.received.append(source.read_bytes())
        if self.error is not None:
            raise self.error
        output_dir.mkdir(parents=True, exist_ok=True)
        playlist = MasterPlaylist.of([Variant(640, 360, 900000, "360p/index.m3u8")])
        (output_dir / "master.m3u8").write_text(playlist.render(), encoding="utf-8")
        return playlist


@pytest.fixture
def transcoder() -> Iterator[FakeTranscoder]:
    fake = FakeTranscoder()
    app.dependency_overrides[get_transcoder] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_transcoder, None)


@pytest.fixture
def catalog() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        movie = make_title(session, "Heat")
        series = make_title(session, "Dark", kind=TitleKind.SERIES.value)
        season = add_season(session, series, 1, ["Secrets"])
        return {"movie": movie.id, "series": series.id, "episode": season.episodes[0].id}


def upload(client: TestClient, path: str, headers: dict[str, str], name: str = "movie.mp4", data: bytes = MP4):
    return client.post(path, files={"file": (name, data, "video/mp4")}, headers=headers)


def asset_status(client: TestClient, asset_id: int, headers: dict[str, str]) -> dict[str, object]:
    r = client.get(f"/api/admin/video-assets/{asset_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_movie_upload_is_transcoded_in_background(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    r = upload(client, f"/api/admin/titles/{catalog['movie']}/video", admin_headers)

    assert r.status_code == 202, r.text
    body = r.json()
    assert (body["title_id"], body["episode_id"], body["status"]) == (catalog["movie"], None, "pending")
    assert asset_status(client, body["id"], admin_headers) == {
        "id": body["id"], "title_id": catalog["movie"], "episode_id": None, "status": "ready",
        "error_message": None, "hls_path": f"hls/{body['id']}/master.m3u8",
    }
    assert [p.name for p in transcoder.calls] == ["source.mp4"]
    assert transcoder.received == [MP4]
    assert not transcoder.calls[0].parent.exists()
    assert (MEDIA / "hls" / str(body["id"]) / "master.m3u8").is_file()


def test_episode_upload_accepts_matroska(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    r = upload(client, f"/api/admin/episodes/{catalog['episode']}/video", admin_headers, "ep1.mkv", MKV)

    assert r.status_code == 202, r.text
    status = asset_status(client, r.json()["id"], admin_headers)
    assert (status["title_id"], status["episode_id"], status["status"]) == (None, catalog["episode"], "ready")


def test_failed_transcoding_is_reported(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    transcoder.error = TranscodeError("ffmpeg exited with code 1: broken input")

    asset_id = upload(client, f"/api/admin/titles/{catalog['movie']}/video", admin_headers).json()["id"]

    status = asset_status(client, asset_id, admin_headers)
    assert (status["status"], status["error_message"], status["hls_path"]) == (
        "failed", "ffmpeg exited with code 1: broken input", None,
    )


def test_reupload_reuses_asset_and_clears_previous_error(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    path = f"/api/admin/titles/{catalog['movie']}/video"
    transcoder.error = TranscodeError("first attempt failed")
    first = upload(client, path, admin_headers).json()["id"]
    transcoder.error = None

    second = upload(client, path, admin_headers).json()["id"]

    assert first == second
    assert asset_status(client, second, admin_headers)["status"] == "ready"
    assert asset_status(client, second, admin_headers)["error_message"] is None
    assert len(transcoder.calls) == 2


def test_upload_while_processing_conflicts(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    with SessionLocal() as session, session.begin():
        session.add(VideoAsset(title_id=catalog["movie"], status=VideoStatus.PROCESSING))

    r = upload(client, f"/api/admin/titles/{catalog['movie']}/video", admin_headers)

    assert_error(r, 409, "video_processing")
    assert transcoder.calls == []


def test_series_title_takes_videos_per_episode(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    assert_error(upload(client, f"/api/admin/titles/{catalog['series']}/video", admin_headers), 409, "not_a_movie")


@pytest.mark.parametrize(
    ("name", "data"),
    [("movie.avi", MP4), ("movie.mp4", b"plain text, not a video"), ("movie.mkv", MP4), ("movie", MP4)],
)
def test_unsupported_files_are_rejected(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder,
    name: str, data: bytes,
) -> None:
    r = upload(client, f"/api/admin/titles/{catalog['movie']}/video", admin_headers, name, data)

    assert_error(r, 415, "unsupported_media_type")


def test_upload_over_size_limit_is_rejected(
    client: TestClient, admin_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    app.dependency_overrides[get_video_upload_limit] = lambda: 32
    try:
        r = upload(client, f"/api/admin/titles/{catalog['movie']}/video", admin_headers)
    finally:
        app.dependency_overrides.pop(get_video_upload_limit)

    assert_error(r, 413, "payload_too_large")
    assert_error(client.get("/api/admin/video-assets/1", headers=admin_headers), 404, "video_asset_not_found")
    assert not (MEDIA / "uploads" / "1").exists()
    assert transcoder.calls == []


@pytest.mark.parametrize(
    ("path", "code"),
    [("/api/admin/titles/999/video", "title_not_found"), ("/api/admin/episodes/999/video", "episode_not_found")],
)
def test_upload_for_unknown_owner_returns_404(
    client: TestClient, admin_headers: dict[str, str], transcoder: FakeTranscoder, path: str, code: str
) -> None:
    assert_error(upload(client, path, admin_headers), 404, code)


def test_video_endpoints_require_admin(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int], transcoder: FakeTranscoder
) -> None:
    assert_error(upload(client, f"/api/admin/titles/{catalog['movie']}/video", user_headers), 403, "forbidden")
    assert_error(upload(client, f"/api/admin/titles/{catalog['movie']}/video", {}), 401, "unauthorized")
    assert_error(client.get("/api/admin/video-assets/1", headers=user_headers), 403, "forbidden")


def make_asset(owner_id: int, status: VideoStatus) -> int:
    with SessionLocal() as session, session.begin():
        asset = VideoAsset(title_id=owner_id, status=status)
        session.add(asset)
        session.flush()
        return asset.id


def processor(transcoder: FakeTranscoder) -> VideoProcessingService:
    return VideoProcessingService(video_asset_transaction, transcoder, LocalVideoStore(MEDIA))


def get_asset(asset_id: int) -> VideoAsset:
    with SessionLocal() as session:
        asset = session.get(VideoAsset, asset_id)
        assert asset is not None
        return asset


def test_fail_interrupted_marks_only_processing_assets() -> None:
    with SessionLocal() as session, session.begin():
        ids = [make_title(session, f"Movie {i}").id for i in range(3)]
    stuck = make_asset(ids[0], VideoStatus.PROCESSING)
    ready = make_asset(ids[1], VideoStatus.READY)
    pending = make_asset(ids[2], VideoStatus.PENDING)

    assert processor(FakeTranscoder()).fail_interrupted() == 1

    assert (get_asset(stuck).status, get_asset(stuck).error_message) == ("failed", INTERRUPTED_MESSAGE)
    assert get_asset(ready).status == "ready"
    assert get_asset(pending).status == "pending"


def test_process_without_source_file_fails(catalog: dict[str, int]) -> None:
    fake = FakeTranscoder()
    asset_id = make_asset(catalog["movie"], VideoStatus.PENDING)

    assert processor(fake).process(asset_id) is VideoStatus.FAILED

    assert get_asset(asset_id).error_message == "Source file is missing"
    assert fake.calls == []


def test_process_ignores_assets_that_are_not_pending(catalog: dict[str, int]) -> None:
    fake = FakeTranscoder()
    asset_id = make_asset(catalog["movie"], VideoStatus.READY)

    assert processor(fake).process(asset_id) is None
    assert processor(fake).process(999) is None
    assert fake.calls == []


def test_process_records_unexpected_errors(catalog: dict[str, int]) -> None:
    fake = FakeTranscoder()
    fake.error = OSError("disk full")
    asset_id = make_asset(catalog["movie"], VideoStatus.PENDING)
    LocalVideoStore(MEDIA).save_source(asset_id, io.BytesIO(MP4), "mp4", 1024)

    assert processor(fake).process(asset_id) is VideoStatus.FAILED
    assert get_asset(asset_id).error_message == "disk full"
