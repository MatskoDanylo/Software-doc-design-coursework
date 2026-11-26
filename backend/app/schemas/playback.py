from pydantic import BaseModel

from app.patterns.playback_proxy import Playback


class AdBreakRead(BaseModel):
    enabled: bool
    preroll_url: str | None


class PlaybackRead(BaseModel):
    plan: str | None
    manifest_url: str
    ads: AdBreakRead
    allowed_heights: list[int]
    resume_position_sec: int

    @classmethod
    def from_playback(cls, playback: Playback) -> "PlaybackRead":
        return cls(
            plan=playback.plan_code,
            manifest_url=f"/api/playback/{playback.asset_id}/master.m3u8",
            ads=AdBreakRead(enabled=playback.ads.enabled, preroll_url=playback.ads.preroll_url),
            allowed_heights=playback.manifest.heights,
            resume_position_sec=playback.resume_position_sec,
        )
