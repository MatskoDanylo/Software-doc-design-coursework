from pydantic import BaseModel

from app.schemas.catalog import TitleRead

MAX_RECOMMENDATIONS = 50
DEFAULT_RECOMMENDATIONS = 12


class RecommendationRead(TitleRead):
    reason: str = ""
    score: float = 0.0


class RecommendationList(BaseModel):
    strategy: str
    items: list[RecommendationRead]
