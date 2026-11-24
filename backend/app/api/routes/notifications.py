from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, NotificationInboxDep
from app.schemas.notification import MAX_NOTIFICATIONS_LIMIT, NotificationList, NotificationRead, ReadAllResult

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    user: CurrentUser,
    inbox: NotificationInboxDep,
    unread_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=MAX_NOTIFICATIONS_LIMIT)] = 50,
) -> NotificationList:
    return NotificationList.model_validate(inbox.list(user, unread_only, limit))


@router.post("/read-all")
def mark_all_read(user: CurrentUser, inbox: NotificationInboxDep) -> ReadAllResult:
    return ReadAllResult(updated=inbox.mark_all_read(user))


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, user: CurrentUser, inbox: NotificationInboxDep) -> NotificationRead:
    return NotificationRead.model_validate(inbox.mark_read(user, notification_id))
