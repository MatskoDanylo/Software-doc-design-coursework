from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, HistoryServiceDep
from app.schemas.history import MAX_HISTORY_LIMIT, HistoryEntryRead, ProgressUpdate

router = APIRouter(prefix="/history", tags=["history"])


@router.put("/progress")
def record_progress(data: ProgressUpdate, user: CurrentUser, history: HistoryServiceDep) -> HistoryEntryRead:
    return history.record_progress(user, data).entry


@router.get("")
def continue_watching(
    user: CurrentUser,
    history: HistoryServiceDep,
    limit: Annotated[int, Query(ge=1, le=MAX_HISTORY_LIMIT)] = 20,
) -> list[HistoryEntryRead]:
    return history.continue_watching(user, limit)
