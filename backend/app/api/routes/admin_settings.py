from fastapi import APIRouter, Depends

from app.api.deps import SettingsServiceDep, require_admin
from app.schemas.settings import AppSettingsRead, AppSettingsUpdate

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/settings")
def get_settings(settings: SettingsServiceDep) -> AppSettingsRead:
    return settings.get()


@router.put("/settings")
def update_settings(data: AppSettingsUpdate, settings: SettingsServiceDep) -> AppSettingsRead:
    return settings.update(data)
