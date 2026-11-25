from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import OptionalUser, RecommendationServiceDep
from app.schemas.recommendation import (
    DEFAULT_RECOMMENDATIONS, MAX_RECOMMENDATIONS, RecommendationList, RecommendationRead,
)

router = APIRouter(tags=["recommendations"])

LimitQuery = Annotated[int, Query(ge=1, le=MAX_RECOMMENDATIONS)]


@router.get("/recommendations")
def recommend(
    service: RecommendationServiceDep,
    user: OptionalUser,
    limit: LimitQuery = DEFAULT_RECOMMENDATIONS,
    strategy: Annotated[str | None, Query(max_length=50)] = None,
) -> RecommendationList:
    return service.recommend(user, limit, strategy)


@router.get("/titles/{title_id}/similar")
def similar_titles(
    title_id: int, service: RecommendationServiceDep, user: OptionalUser, limit: LimitQuery = DEFAULT_RECOMMENDATIONS
) -> list[RecommendationRead]:
    return service.similar(title_id, limit, user)
