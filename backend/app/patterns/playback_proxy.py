from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from typing import Protocol

from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.models import User, VideoAsset, VideoStatus
from app.services.hls_playlist import MasterPlaylist
from app.services.playback_target import PlaybackTargetResolver
from app.services.ports import VideoAssetStore, WatchHistoryStore


@dataclass(frozen=True)
class PlaybackPolicy:
    plan_code: str
    max_height: int
    ads_enabled: bool


@dataclass(frozen=True)
class AdBreak:
    enabled: bool
    preroll_url: str | None


NO_ADS = AdBreak(enabled=False, preroll_url=None)


@dataclass(frozen=True)
class Playback:
    asset_id: int
    manifest: MasterPlaylist
    ads: AdBreak
    resume_position_sec: int
    plan_code: str | None = None


class PlaybackPolicyProvider(Protocol):
    def policy_for(self, user: User) -> PlaybackPolicy: ...


class AdProvider(Protocol):
    def preroll_url(self) -> str | None: ...


class ManifestSource(Protocol):
    def read(self, relative_path: str) -> str | None: ...

    def base_url(self, relative_path: str) -> str: ...


class PlaybackService(ABC):
    @abstractmethod
    def get_playback(self, user: User | None, title_id: int, episode_id: int | None) -> Playback: ...

    @abstractmethod
    def get_master_manifest(self, user: User | None, asset_id: int) -> MasterPlaylist: ...


class RealPlaybackService(PlaybackService):
    def __init__(
        self,
        targets: PlaybackTargetResolver,
        assets: VideoAssetStore,
        manifests: ManifestSource,
        history: WatchHistoryStore,
    ) -> None:
        self.targets = targets
        self.assets = assets
        self.manifests = manifests
        self.history = history

    def get_playback(self, user: User | None, title_id: int, episode_id: int | None) -> Playback:
        target = self.targets.resolve(title_id, episode_id)
        if target.episode is not None:
            asset = self.assets.get_by_episode(target.episode.id)
        else:
            asset = self.assets.get_by_title(target.title.id)
        ready = self._require_ready(asset)
        resume = self._resume_position(user, target.title.id, target.episode_id)
        return Playback(asset_id=ready.id, manifest=self._load(ready), ads=NO_ADS, resume_position_sec=resume)

    def get_master_manifest(self, user: User | None, asset_id: int) -> MasterPlaylist:
        asset = self.assets.get(asset_id)
        if asset is None:
            raise NotFoundError("Video not found", code="video_not_found")
        return self._load(self._require_ready(asset))

    @staticmethod
    def _require_ready(asset: VideoAsset | None) -> VideoAsset:
        if asset is None:
            raise NotFoundError("Video for this title has not been uploaded yet", code="video_not_ready")
        if asset.status == VideoStatus.FAILED:
            raise NotFoundError("Video processing failed; the video is unavailable", code="video_not_ready")
        if asset.status != VideoStatus.READY:
            raise NotFoundError("Video is still being processed; try again later", code="video_not_ready")
        return asset

    def _load(self, asset: VideoAsset) -> MasterPlaylist:
        text = self.manifests.read(asset.hls_path) if asset.hls_path else None
        if asset.hls_path is None or text is None:
            raise NotFoundError("Video files are missing on the server", code="video_not_ready")
        return MasterPlaylist.parse(text).with_uri_prefix(self.manifests.base_url(asset.hls_path))

    def _resume_position(self, user: User | None, title_id: int, episode_id: int | None) -> int:
        if user is None:
            return 0
        entry = self.history.get_entry(user.id, title_id, episode_id)
        return 0 if entry is None or entry.finished else entry.progress_sec


class PlaybackProxy(PlaybackService):
    def __init__(self, real: PlaybackService, policies: PlaybackPolicyProvider, ads: AdProvider) -> None:
        self.real = real
        self.policies = policies
        self.ads = ads

    def get_playback(self, user: User | None, title_id: int, episode_id: int | None) -> Playback:
        policy = self._policy(user)
        playback = self.real.get_playback(user, title_id, episode_id)
        preroll = self.ads.preroll_url() if policy.ads_enabled else None
        return replace(
            playback,
            manifest=self._restrict(playback.manifest, policy),
            ads=AdBreak(enabled=preroll is not None, preroll_url=preroll),
            plan_code=policy.plan_code,
        )

    def get_master_manifest(self, user: User | None, asset_id: int) -> MasterPlaylist:
        policy = self._policy(user)
        return self._restrict(self.real.get_master_manifest(user, asset_id), policy)

    def _policy(self, user: User | None) -> PlaybackPolicy:
        if user is None:
            raise UnauthorizedError("Sign in to watch videos")
        return self.policies.policy_for(user)

    @staticmethod
    def _restrict(manifest: MasterPlaylist, policy: PlaybackPolicy) -> MasterPlaylist:
        allowed = manifest.limited_to(policy.max_height)
        if not allowed.variants:
            raise ForbiddenError(
                f"No video quality is available on the {policy.plan_code} plan", code="quality_not_available"
            )
        return allowed
