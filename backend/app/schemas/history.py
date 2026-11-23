from datetime import datetime

from pydantic import AliasPath, BaseModel, ConfigDict, Field

from app.schemas.catalog import TitleRead

MAX_PROGRESS_SEC = 24 * 60 * 60
MAX_HISTORY_LIMIT = 50


class ProgressUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title_id: int
    episode_id: int | None = None
    progress_sec: int = Field(ge=0, le=MAX_PROGRESS_SEC)
    finished: bool = False


class HistoryEpisodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    name: str
    season_number: int = Field(validation_alias=AliasPath("season", "number"))


class HistoryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: TitleRead
    episode: HistoryEpisodeRead | None
    progress_sec: int
    finished: bool
    last_watched: datetime
