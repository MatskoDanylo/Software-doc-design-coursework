from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import OptionalUser, PlaybackServiceDep, StreamUser
from app.schemas.playback import PlaybackRead

router = APIRouter(tags=["playback"])

HLS_MEDIA_TYPE = "application/vnd.apple.mpegurl"


@router.get("/titles/{title_id}/playback")
def get_playback(
    title_id: int,
    user: OptionalUser,
    playback: PlaybackServiceDep,
    episode_id: Annotated[int | None, Query()] = None,
) -> PlaybackRead:
    return PlaybackRead.from_playback(playback.get_playback(user, title_id, episode_id))


@router.get("/playback/{asset_id}/master.m3u8", response_class=Response)
def get_master_manifest(asset_id: int, user: StreamUser, playback: PlaybackServiceDep) -> Response:
    manifest = playback.get_master_manifest(user, asset_id)
    return Response(manifest.render(), media_type=HLS_MEDIA_TYPE, headers={"Cache-Control": "no-store"})
