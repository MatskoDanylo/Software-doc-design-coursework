from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import NotificationKind

MAX_NOTIFICATIONS_LIMIT = 100


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: NotificationKind
    message: str
    read: bool
    created_at: datetime


class NotificationList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[NotificationRead]
    unread: int


class ReadAllResult(BaseModel):
    updated: int
