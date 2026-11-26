from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, status

from app.api.deps import VideoProcessorDep, VideoUploadServiceDep, require_admin
from app.schemas.video import VideoAssetRead

router = APIRouter(prefix="/admin", tags=["admin: video"], dependencies=[Depends(require_admin)])


@router.post("/titles/{title_id}/video", status_code=status.HTTP_202_ACCEPTED)
def upload_title_video(
    title_id: int,
    file: UploadFile,
    uploads: VideoUploadServiceDep,
    processor: VideoProcessorDep,
    background: BackgroundTasks,
) -> VideoAssetRead:
    asset = uploads.upload_for_title(title_id, file.file, file.filename)
    background.add_task(processor.process, asset.id)
    return asset


@router.post("/episodes/{episode_id}/video", status_code=status.HTTP_202_ACCEPTED)
def upload_episode_video(
    episode_id: int,
    file: UploadFile,
    uploads: VideoUploadServiceDep,
    processor: VideoProcessorDep,
    background: BackgroundTasks,
) -> VideoAssetRead:
    asset = uploads.upload_for_episode(episode_id, file.file, file.filename)
    background.add_task(processor.process, asset.id)
    return asset


@router.get("/titles/{title_id}/video")
def get_title_video(title_id: int, uploads: VideoUploadServiceDep) -> VideoAssetRead:
    return uploads.get_for_title(title_id)


@router.get("/episodes/{episode_id}/video")
def get_episode_video(episode_id: int, uploads: VideoUploadServiceDep) -> VideoAssetRead:
    return uploads.get_for_episode(episode_id)


@router.get("/video-assets/{asset_id}")
def get_video_asset(asset_id: int, uploads: VideoUploadServiceDep) -> VideoAssetRead:
    return uploads.get_asset(asset_id)
