from pydantic import BaseModel, ConfigDict

from app.models import VideoStatus


class VideoAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title_id: int | None
    episode_id: int | None
    status: VideoStatus
    error_message: str | None
    hls_path: str | None
    duration_sec: int | None
