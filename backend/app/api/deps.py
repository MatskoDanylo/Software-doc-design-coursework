from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.storage import FileStorage, LocalMediaStorage, LocalVideoStore, VideoFileStore
from app.models import Role, User
from app.repositories.genre_repository import GenreRepository
from app.repositories.season_repository import EpisodeRepository, SeasonRepository
from app.repositories.title_repository import TitleRepository
from app.repositories.users import UserRepository
from app.repositories.video_asset_repository import VideoAssetRepository, video_asset_transaction
from app.services.admin_catalog_service import AdminCatalogService
from app.services.auth import AuthService
from app.services.catalog_service import CatalogService
from app.services.hls_transcoder import HlsTranscoder, VideoTranscoder
from app.services.poster_service import PosterService
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
    return CatalogService(TitleRepository(session), GenreRepository(session))


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


def require_admin(user: CurrentUser) -> User:
    if user.role != Role.ADMIN:
        raise ForbiddenError("Administrator role required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
