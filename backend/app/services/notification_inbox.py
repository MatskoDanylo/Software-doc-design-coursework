from collections.abc import Sequence
from dataclasses import dataclass

from app.core.errors import NotFoundError
from app.models import Notification, User
from app.services.ports import NotificationStore


@dataclass(frozen=True)
class Inbox:
    items: Sequence[Notification]
    unread: int


class NotificationInbox:
    def __init__(self, notifications: NotificationStore) -> None:
        self.notifications = notifications

    def list(self, user: User, unread_only: bool, limit: int) -> Inbox:
        return Inbox(
            items=self.notifications.list_for_user(user.id, unread_only, limit),
            unread=self.notifications.unread_count(user.id),
        )

    def mark_read(self, user: User, notification_id: int) -> Notification:
        notification = self.notifications.get_for_user(notification_id, user.id)
        if notification is None:
            raise NotFoundError("Notification not found", code="notification_not_found")
        notification.read = True
        return self.notifications.save(notification)

    def mark_all_read(self, user: User) -> int:
        return self.notifications.mark_all_read(user.id)
