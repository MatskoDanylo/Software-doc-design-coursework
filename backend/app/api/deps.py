from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.events import EventBus
from app.core.storage import (
    FileStorage, LocalAdProvider, LocalManifestSource, LocalMediaStorage, LocalVideoStore, VideoFileStore,
)
from app.event_wiring import create_event_bus
from app.models import Role, User
from app.patterns.payment_gateway import MockGatewayAdapter, MockPaymentProvider
from app.patterns.plan_factory import PlanPolicyRegistry, default_plan_registry
from app.patterns.playback_proxy import PlaybackProxy, PlaybackService, RealPlaybackService
from app.patterns.recommendation import StrategyRegistry, default_strategy_registry
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.genre_repository import GenreRepository
from app.repositories.history_repository import WatchHistoryRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.plans import PlanRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.season_repository import EpisodeRepository, SeasonRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.title_repository import TitleRepository
from app.repositories.users import UserRepository
from app.repositories.video_asset_repository import VideoAssetRepository, video_asset_transaction
from app.services.admin_catalog_service import AdminCatalogService
from app.services.auth import AuthService
from app.services.billing_service import BillingService
from app.services.catalog_service import CatalogService
from app.services.favorite_service import FavoriteService
from app.services.history_service import HistoryService
from app.services.notification_inbox import NotificationInbox
from app.services.hls_transcoder import HlsTranscoder, VideoTranscoder
from app.services.playback_target import PlaybackTargetResolver
from app.services.poster_service import PosterService
from app.services.recommendation_service import (
    RecommendationConfigProvider, RecommendationService, StaticRecommendationConfig,
)
from app.services.subscription_service import SubscriptionService
from app.services.users import UserService
from app.services.video_service import VideoProcessingService, VideoUploadService

SessionDep = Annotated[Session, Depends(get_db, scope="function")]
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(UserRepository(session))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_auth_service(session: SessionDep, user_service: UserServiceDep) -> AuthService:
    return AuthService(UserRepository(session), user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_catalog_service(session: SessionDep) -> CatalogService:
    return CatalogService(TitleRepository(session), GenreRepository(session), FavoriteRepository(session))


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]


def get_media_storage() -> FileStorage:
    return LocalMediaStorage(Path(settings.media_dir))


MediaStorageDep = Annotated[FileStorage, Depends(get_media_storage)]


def get_admin_catalog_service(session: SessionDep, storage: MediaStorageDep) -> AdminCatalogService:
    return AdminCatalogService(
        TitleRepository(session),
        GenreRepository(session),
        SeasonRepository(session),
        EpisodeRepository(session),
        storage,
    )


AdminCatalogServiceDep = Annotated[AdminCatalogService, Depends(get_admin_catalog_service)]


def get_poster_service(session: SessionDep, storage: MediaStorageDep) -> PosterService:
    return PosterService(TitleRepository(session), storage)


PosterServiceDep = Annotated[PosterService, Depends(get_poster_service)]


def get_video_store() -> VideoFileStore:
    return LocalVideoStore(Path(settings.media_dir))


VideoStoreDep = Annotated[VideoFileStore, Depends(get_video_store)]


def get_transcoder() -> VideoTranscoder:
    return HlsTranscoder(settings.ffmpeg_path, settings.ffmpeg_timeout_sec)


def get_video_upload_limit() -> int:
    return settings.max_video_upload_mb * 1024 * 1024


def get_video_upload_service(
    session: SessionDep, store: VideoStoreDep, max_bytes: Annotated[int, Depends(get_video_upload_limit)]
) -> VideoUploadService:
    return VideoUploadService(
        TitleRepository(session), EpisodeRepository(session), VideoAssetRepository(session), store, max_bytes
    )


VideoUploadServiceDep = Annotated[VideoUploadService, Depends(get_video_upload_service)]


def get_video_processor(
    transcoder: Annotated[VideoTranscoder, Depends(get_transcoder)], store: VideoStoreDep
) -> VideoProcessingService:
    return VideoProcessingService(video_asset_transaction, transcoder, store)


VideoProcessorDep = Annotated[VideoProcessingService, Depends(get_video_processor)]


def get_current_user(credentials: BearerDep, auth: AuthServiceDep) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")
    return auth.authenticate(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_optional_user(credentials: BearerDep, auth: AuthServiceDep) -> User | None:
    return None if credentials is None else auth.authenticate(credentials.credentials)


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def get_stream_user(
    credentials: BearerDep,
    auth: AuthServiceDep,
    access_token: Annotated[str | None, Query(description="Access token for players that cannot set headers")] = None,
) -> User | None:
    token = credentials.credentials if credentials is not None else access_token
    return None if token is None else auth.authenticate(token)


StreamUser = Annotated[User | None, Depends(get_stream_user)]


@lru_cache
def get_plan_policies() -> PlanPolicyRegistry:
    return default_plan_registry(settings.premium_days)


PlanPoliciesDep = Annotated[PlanPolicyRegistry, Depends(get_plan_policies)]


def get_event_bus(session: SessionDep, plan_policies: PlanPoliciesDep) -> EventBus:
    return create_event_bus(session, plan_policies)


EventBusDep = Annotated[EventBus, Depends(get_event_bus)]


def get_subscription_service(
    session: SessionDep, plan_policies: PlanPoliciesDep, events: EventBusDep
) -> SubscriptionService:
    return SubscriptionService(SubscriptionRepository(session), PlanRepository(session), plan_policies, events)


SubscriptionServiceDep = Annotated[SubscriptionService, Depends(get_subscription_service)]


@lru_cache
def get_mock_gateway() -> MockGatewayAdapter:
    return MockGatewayAdapter(MockPaymentProvider())


def get_billing_service(
    session: SessionDep,
    gateway: Annotated[MockGatewayAdapter, Depends(get_mock_gateway)],
    plan_policies: PlanPoliciesDep,
    subscriptions: SubscriptionServiceDep,
    events: EventBusDep,
) -> BillingService:
    return BillingService(
        PaymentRepository(session), PlanRepository(session), gateway, gateway, plan_policies, subscriptions, events
    )


BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]


def get_notification_inbox(session: SessionDep) -> NotificationInbox:
    return NotificationInbox(NotificationRepository(session))


NotificationInboxDep = Annotated[NotificationInbox, Depends(get_notification_inbox)]


def require_mock_payments() -> None:
    if not settings.payments_mock_enabled:
        raise NotFoundError("Mock payments are disabled", code="mock_payments_disabled")


def get_playback_service(session: SessionDep, subscriptions: SubscriptionServiceDep) -> PlaybackService:
    media_root = Path(settings.media_dir)
    real = RealPlaybackService(
        PlaybackTargetResolver(TitleRepository(session), EpisodeRepository(session)),
        VideoAssetRepository(session),
        LocalManifestSource(media_root),
        WatchHistoryRepository(session),
    )
    return PlaybackProxy(real, subscriptions, LocalAdProvider(media_root))


PlaybackServiceDep = Annotated[PlaybackService, Depends(get_playback_service)]


def get_favorite_service(session: SessionDep) -> FavoriteService:
    return FavoriteService(FavoriteRepository(session), TitleRepository(session))


FavoriteServiceDep = Annotated[FavoriteService, Depends(get_favorite_service)]


def get_history_service(session: SessionDep, events: EventBusDep) -> HistoryService:
    return HistoryService(
        WatchHistoryRepository(session),
        PlaybackTargetResolver(TitleRepository(session), EpisodeRepository(session)),
        FavoriteRepository(session),
        events,
    )


HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]


@lru_cache
def get_strategy_registry() -> StrategyRegistry:
    return default_strategy_registry()


StrategyRegistryDep = Annotated[StrategyRegistry, Depends(get_strategy_registry)]


def get_recommendation_config() -> RecommendationConfigProvider:
    return StaticRecommendationConfig()


def get_recommendation_service(
    session: SessionDep,
    registry: StrategyRegistryDep,
    config: Annotated[RecommendationConfigProvider, Depends(get_recommendation_config)],
) -> RecommendationService:
    source = RecommendationRepository(session)
    return RecommendationService(
        registry, source, source, TitleRepository(session), FavoriteRepository(session), config
    )


RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


def require_admin(user: CurrentUser) -> User:
    if user.role != Role.ADMIN:
        raise ForbiddenError("Administrator role required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
