import shutil
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.storage import LocalAdProvider
from app.models import PlanCode, Subscription, TitleKind, User, VideoAsset, VideoStatus, WatchHistory
from app.patterns.plan_factory import default_plan_registry
from app.patterns.playback_proxy import (
    NO_ADS,
    AdBreak,
    Playback,
    PlaybackPolicy,
    PlaybackProxy,
    PlaybackService,
)
from app.repositories.plans import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.users import UserRepository
from app.services.hls_playlist import MasterPlaylist, Variant
from app.services.subscription_service import SubscriptionService
from tests.factories import add_season, make_title
from tests.helpers import assert_error, bearer

MEDIA = Path(settings.media_dir)
MASTER = MasterPlaylist.of([
    Variant(640, 360, 900_000, "360p/index.m3u8", "avc1.64001f,mp4a.40.2"),
    Variant(1280, 720, 3_000_000, "720p/index.m3u8", "avc1.64001f,mp4a.40.2"),
    Variant(1920, 1080, 5_500_000, "1080p/index.m3u8", "avc1.640028,mp4a.40.2"),
])
FREE = PlaybackPolicy("free", max_height=720, ads_enabled=True)
PREMIUM = PlaybackPolicy("premium", max_height=1080, ads_enabled=False)
AD_URL = "/media/ads/preroll/master.m3u8"


class FakeRealPlayback(PlaybackService):
    def __init__(self) -> None:
        self.calls = 0

    def get_playback(self, user: User | None, title_id: int, episode_id: int | None) -> Playback:
        self.calls += 1
        return Playback(asset_id=7, manifest=MASTER, ads=NO_ADS, resume_position_sec=42)

    def get_master_manifest(self, user: User | None, asset_id: int) -> MasterPlaylist:
        self.calls += 1
        return MASTER


class FixedPolicy:
    def __init__(self, policy: PlaybackPolicy) -> None:
        self.policy = policy

    def policy_for(self, user: User) -> PlaybackPolicy:
        return self.policy


class FixedAds:
    def __init__(self, url: str | None) -> None:
        self.url = url

    def preroll_url(self) -> str | None:
        return self.url


def proxy(policy: PlaybackPolicy, ad_url: str | None = AD_URL) -> tuple[PlaybackProxy, FakeRealPlayback]:
    real = FakeRealPlayback()
    return PlaybackProxy(real, FixedPolicy(policy), FixedAds(ad_url)), real


VIEWER = User(id=1, email="viewer@example.com")


def test_free_plan_is_limited_to_720p_with_preroll() -> None:
    playback = proxy(FREE)[0].get_playback(VIEWER, 1, None)

    assert playback.manifest.heights == [360, 720]
    assert playback.ads == AdBreak(enabled=True, preroll_url=AD_URL)
    assert (playback.asset_id, playback.resume_position_sec, playback.plan_code) == (7, 42, "free")


def test_premium_plan_gets_1080p_without_ads() -> None:
    playback = proxy(PREMIUM)[0].get_playback(VIEWER, 1, None)

    assert playback.manifest.heights == [360, 720, 1080]
    assert playback.ads == NO_ADS
    assert playback.plan_code == "premium"


def test_ads_are_disabled_when_no_preroll_exists() -> None:
    assert proxy(FREE, ad_url=None)[0].get_playback(VIEWER, 1, None).ads == NO_ADS


def test_master_manifest_is_filtered_by_the_same_policy() -> None:
    assert proxy(FREE)[0].get_master_manifest(VIEWER, 7).heights == [360, 720]
    assert proxy(PREMIUM)[0].get_master_manifest(VIEWER, 7).heights == [360, 720, 1080]


def test_guest_is_rejected_before_reaching_real_service() -> None:
    playback_proxy, real = proxy(FREE)

    with pytest.raises(UnauthorizedError):
        playback_proxy.get_playback(None, 1, None)
    with pytest.raises(UnauthorizedError):
        playback_proxy.get_master_manifest(None, 7)
    assert real.calls == 0


def test_plan_without_any_matching_rendition_is_forbidden() -> None:
    with pytest.raises(ForbiddenError) as error:
        proxy(PlaybackPolicy("tiny", max_height=240, ads_enabled=True))[0].get_master_manifest(VIEWER, 7)

    assert error.value.code == "quality_not_available"


def write_hls(asset_id: int) -> str:
    folder = MEDIA / "hls" / str(asset_id)
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    (folder / "master.m3u8").write_text(MASTER.render(), encoding="utf-8")
    return f"hls/{asset_id}/master.m3u8"


def add_asset(
    title_id: int | None = None, episode_id: int | None = None, status: VideoStatus = VideoStatus.READY
) -> int:
    with SessionLocal() as session, session.begin():
        asset = VideoAsset(title_id=title_id, episode_id=episode_id, status=status)
        session.add(asset)
        session.flush()
        if status is VideoStatus.READY:
            asset.hls_path = write_hls(asset.id)
        return asset.id


@pytest.fixture
def catalog() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        movie = make_title(session, "Heat")
        empty = make_title(session, "Ronin")
        series = make_title(session, "Dark", kind=TitleKind.SERIES.value)
        other = make_title(session, "Lost", kind=TitleKind.SERIES.value)
        episode = add_season(session, series, 1, ["Secrets"]).episodes[0]
        foreign = add_season(session, other, 1, ["Pilot"]).episodes[0]
        ids = {"movie": movie.id, "empty": empty.id, "series": series.id, "episode": episode.id,
               "foreign_episode": foreign.id}
    ids["asset"] = add_asset(title_id=ids["movie"])
    ids["episode_asset"] = add_asset(episode_id=ids["episode"])
    return ids


@pytest.fixture
def preroll() -> Iterator[None]:
    path = MEDIA / LocalAdProvider.PREROLL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#EXTM3U\n", encoding="utf-8")
    yield
    shutil.rmtree(MEDIA / "ads", ignore_errors=True)


@pytest.fixture
def viewer(client: TestClient, seeded: None, user_headers: dict[str, str]) -> dict[str, str]:
    return user_headers


def grant_premium(email: str = "user@example.com", days: int = 30) -> None:
    with SessionLocal() as session, session.begin():
        user = UserRepository(session).get_by_email(email)
        assert user is not None
        SubscriptionService(SubscriptionRepository(session), PlanRepository(session), default_plan_registry(30)).grant(
            user, PlanCode.PREMIUM, days
        )


def playback(client: TestClient, title_id: int, headers: dict[str, str], **params: int) -> dict[str, object]:
    r = client.get(f"/api/titles/{title_id}/playback", params=params, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_free_user_gets_720p_and_preroll(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int], preroll: None
) -> None:
    assert playback(client, catalog["movie"], viewer) == {
        "plan": "free",
        "manifest_url": f"/api/playback/{catalog['asset']}/master.m3u8",
        "ads": {"enabled": True, "preroll_url": AD_URL},
        "allowed_heights": [360, 720],
        "resume_position_sec": 0,
    }


def test_free_user_without_generated_ad_sees_no_ads(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int]
) -> None:
    assert playback(client, catalog["movie"], viewer)["ads"] == {"enabled": False, "preroll_url": None}


def test_premium_user_gets_1080p_without_ads(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int], preroll: None
) -> None:
    grant_premium()

    body = playback(client, catalog["movie"], viewer)

    assert body["plan"] == "premium"
    assert body["allowed_heights"] == [360, 720, 1080]
    assert body["ads"] == {"enabled": False, "preroll_url": None}


def test_expired_subscription_falls_back_to_free(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int], preroll: None
) -> None:
    with SessionLocal() as session, session.begin():
        user = UserRepository(session).get_by_email("user@example.com")
        premium = PlanRepository(session).get_by_code(PlanCode.PREMIUM)
        assert user is not None and premium is not None
        session.add(Subscription(user_id=user.id, plan_id=premium.id, status="active",
                                 expires_at=datetime.now(UTC) - timedelta(minutes=1)))

    body = playback(client, catalog["movie"], viewer)

    assert body["allowed_heights"] == [360, 720]
    assert body["ads"]["enabled"] is True


def test_master_manifest_is_filtered_and_points_to_static_media(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int]
) -> None:
    r = client.get(f"/api/playback/{catalog['asset']}/master.m3u8", headers=viewer)

    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/vnd.apple.mpegurl"
    assert r.headers["cache-control"] == "no-store"
    manifest = MasterPlaylist.parse(r.text)
    assert [v.uri for v in manifest.variants] == [
        f"/media/hls/{catalog['asset']}/360p/index.m3u8",
        f"/media/hls/{catalog['asset']}/720p/index.m3u8",
    ]
    assert "1080p" not in r.text


def test_master_manifest_for_premium_includes_1080p(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int]
) -> None:
    grant_premium()

    r = client.get(f"/api/playback/{catalog['asset']}/master.m3u8", headers=viewer)

    assert MasterPlaylist.parse(r.text).heights == [360, 720, 1080]


def test_master_manifest_accepts_token_in_query(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int]
) -> None:
    token = viewer["Authorization"].removeprefix("Bearer ")

    r = client.get(f"/api/playback/{catalog['asset']}/master.m3u8", params={"access_token": token})

    assert r.status_code == 200, r.text
    assert MasterPlaylist.parse(r.text).heights == [360, 720]


def test_guests_and_invalid_tokens_get_401(client: TestClient, seeded: None, catalog: dict[str, int]) -> None:
    manifest = f"/api/playback/{catalog['asset']}/master.m3u8"

    assert_error(client.get(f"/api/titles/{catalog['movie']}/playback"), 401, "unauthorized")
    assert_error(client.get(manifest), 401, "unauthorized")
    assert_error(client.get(manifest, params={"access_token": "garbage"}), 401, "invalid_token")
    assert_error(client.get(manifest, headers=bearer("garbage")), 401, "invalid_token")


def test_query_token_is_not_accepted_for_playback_info(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int]
) -> None:
    token = viewer["Authorization"].removeprefix("Bearer ")

    r = client.get(f"/api/titles/{catalog['movie']}/playback", params={"access_token": token})

    assert_error(r, 401, "unauthorized")


def test_episode_playback(client: TestClient, viewer: dict[str, str], catalog: dict[str, int]) -> None:
    body = playback(client, catalog["series"], viewer, episode_id=catalog["episode"])

    assert body["manifest_url"] == f"/api/playback/{catalog['episode_asset']}/master.m3u8"


@pytest.mark.parametrize(
    ("title", "params", "status", "code"),
    [
        ("empty", {}, 404, "video_not_ready"),
        ("missing", {}, 404, "title_not_found"),
        ("series", {}, 422, "episode_required"),
        ("movie", {"episode_id": "episode"}, 422, "episode_not_allowed"),
        ("series", {"episode_id": "foreign_episode"}, 404, "episode_not_found"),
    ],
)
def test_playback_errors(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int],
    title: str, params: dict[str, str], status: int, code: str,
) -> None:
    title_id = catalog.get(title, 999)
    query = {key: catalog[value] for key, value in params.items()}

    assert_error(client.get(f"/api/titles/{title_id}/playback", params=query, headers=viewer), status, code)


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (VideoStatus.PENDING, "Video is still being processed; try again later"),
        (VideoStatus.PROCESSING, "Video is still being processed; try again later"),
        (VideoStatus.FAILED, "Video processing failed; the video is unavailable"),
    ],
)
def test_video_that_is_not_ready_returns_clear_404(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int], status: VideoStatus, message: str
) -> None:
    asset_id = add_asset(title_id=catalog["empty"], status=status)

    r = client.get(f"/api/titles/{catalog['empty']}/playback", headers=viewer)

    assert_error(r, 404, "video_not_ready")
    assert r.json()["error"]["message"] == message
    assert_error(client.get(f"/api/playback/{asset_id}/master.m3u8", headers=viewer), 404, "video_not_ready")


def test_unknown_asset_manifest_returns_404(client: TestClient, viewer: dict[str, str], seeded: None) -> None:
    assert_error(client.get("/api/playback/999/master.m3u8", headers=viewer), 404, "video_not_found")


def test_missing_manifest_file_returns_404(client: TestClient, viewer: dict[str, str], catalog: dict[str, int]) -> None:
    shutil.rmtree(MEDIA / "hls" / str(catalog["asset"]))

    assert_error(client.get(f"/api/titles/{catalog['movie']}/playback", headers=viewer), 404, "video_not_ready")


@pytest.mark.parametrize(("finished", "expected"), [(False, 125), (True, 0)])
def test_resume_position_comes_from_unfinished_history(
    client: TestClient, viewer: dict[str, str], catalog: dict[str, int], finished: bool, expected: int
) -> None:
    with SessionLocal() as session, session.begin():
        user = UserRepository(session).get_by_email("user@example.com")
        assert user is not None
        session.add(WatchHistory(user_id=user.id, title_id=catalog["series"], episode_id=catalog["episode"],
                                 progress_sec=125, finished=finished))

    body = playback(client, catalog["series"], viewer, episode_id=catalog["episode"])

    assert body["resume_position_sec"] == expected
    assert playback(client, catalog["movie"], viewer)["resume_position_sec"] == 0
