from sqlalchemy.orm import Session

from app.core.events import EventBus


def create_event_bus(session: Session) -> EventBus:
    return EventBus(session)
