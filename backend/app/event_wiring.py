from sqlalchemy.orm import Session

from app.core.events import (
    EventBus,
    PaymentFailed,
    PaymentPending,
    PaymentSucceeded,
    SubscriptionActivated,
    WatchFinished,
)
from app.patterns.plan_factory import PlanPolicyRegistry
from app.repositories.notification_repository import NotificationRepository
from app.repositories.plans import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.title_stats_repository import TitleStatsRepository
from app.services.notification_service import NotificationService
from app.services.subscription_activator import SubscriptionActivator
from app.services.subscription_service import SubscriptionService
from app.services.title_stats import TitleStatsUpdater


def create_event_bus(session: Session, plan_policies: PlanPolicyRegistry) -> EventBus:
    bus = EventBus(session)

    def subscription_service(unit: Session) -> SubscriptionService:
        return SubscriptionService(SubscriptionRepository(unit), PlanRepository(unit), plan_policies, bus)

    notifications = NotificationService(NotificationRepository)
    bus.subscribe(PaymentSucceeded, SubscriptionActivator(subscription_service))
    bus.subscribe(PaymentPending, notifications)
    bus.subscribe(PaymentFailed, notifications)
    bus.subscribe(SubscriptionActivated, notifications)
    bus.subscribe(WatchFinished, TitleStatsUpdater(TitleStatsRepository))
    return bus
