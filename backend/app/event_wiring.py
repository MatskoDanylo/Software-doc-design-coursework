from sqlalchemy.orm import Session

from app.core.events import EventBus, PaymentFailed, PaymentPending, PaymentSucceeded, SubscriptionActivated
from app.patterns.plan_factory import PlanPolicyRegistry
from app.repositories.notification_repository import NotificationRepository
from app.repositories.plans import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.notification_service import NotificationService
from app.services.subscription_activator import SubscriptionActivator
from app.services.subscription_service import SubscriptionService


def create_event_bus(session: Session, plan_policies: PlanPolicyRegistry) -> EventBus:
    bus = EventBus(session)

    def subscription_service(unit: Session) -> SubscriptionService:
        return SubscriptionService(SubscriptionRepository(unit), PlanRepository(unit), plan_policies, bus)

    notifications = NotificationService(NotificationRepository)
    bus.subscribe(PaymentSucceeded, SubscriptionActivator(subscription_service))
    bus.subscribe(PaymentPending, notifications)
    bus.subscribe(PaymentFailed, notifications)
    bus.subscribe(SubscriptionActivated, notifications)
    return bus
