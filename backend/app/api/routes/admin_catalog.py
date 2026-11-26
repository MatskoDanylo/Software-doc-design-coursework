from fastapi import APIRouter, Depends, UploadFile, status

from app.api.deps import AdminCatalogServiceDep, PosterServiceDep, require_admin
from app.schemas.admin_catalog import (
    EpisodeCreate,
    EpisodeUpdate,
    GenreWrite,
    SeasonCreate,
    SeasonUpdate,
    TitleCreate,
    TitleUpdate,
)
from app.schemas.catalog import EpisodeRead, GenreRead, SeasonRead, TitleDetail, TitleRead
from app.services.poster_service import MAX_POSTER_BYTES

router = APIRouter(prefix="/admin", tags=["admin: catalog"], dependencies=[Depends(require_admin)])


@router.post("/titles", status_code=status.HTTP_201_CREATED)
def create_title(data: TitleCreate, catalog: AdminCatalogServiceDep) -> TitleDetail:
    return catalog.create_title(data)


@router.patch("/titles/{title_id}")
def update_title(title_id: int, data: TitleUpdate, catalog: AdminCatalogServiceDep) -> TitleDetail:
    return catalog.update_title(title_id, data)


@router.delete("/titles/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_title(title_id: int, catalog: AdminCatalogServiceDep) -> None:
    catalog.delete_title(title_id)


@router.post("/titles/{title_id}/poster")
def upload_poster(title_id: int, file: UploadFile, posters: PosterServiceDep) -> TitleRead:
    return posters.upload(title_id, file.file.read(MAX_POSTER_BYTES + 1), file.content_type)


@router.post("/genres", status_code=status.HTTP_201_CREATED)
def create_genre(data: GenreWrite, catalog: AdminCatalogServiceDep) -> GenreRead:
    return catalog.create_genre(data)


@router.patch("/genres/{genre_id}")
def update_genre(genre_id: int, data: GenreWrite, catalog: AdminCatalogServiceDep) -> GenreRead:
    return catalog.update_genre(genre_id, data)


@router.delete("/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(genre_id: int, catalog: AdminCatalogServiceDep) -> None:
    catalog.delete_genre(genre_id)


@router.post("/titles/{title_id}/seasons", status_code=status.HTTP_201_CREATED)
def create_season(title_id: int, data: SeasonCreate, catalog: AdminCatalogServiceDep) -> SeasonRead:
    return catalog.create_season(title_id, data)


@router.patch("/seasons/{season_id}")
def update_season(season_id: int, data: SeasonUpdate, catalog: AdminCatalogServiceDep) -> SeasonRead:
    return catalog.update_season(season_id, data)


@router.delete("/seasons/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_season(season_id: int, catalog: AdminCatalogServiceDep) -> None:
    catalog.delete_season(season_id)


@router.post("/seasons/{season_id}/episodes", status_code=status.HTTP_201_CREATED)
def create_episode(season_id: int, data: EpisodeCreate, catalog: AdminCatalogServiceDep) -> EpisodeRead:
    return catalog.create_episode(season_id, data)


@router.patch("/episodes/{episode_id}")
def update_episode(episode_id: int, data: EpisodeUpdate, catalog: AdminCatalogServiceDep) -> EpisodeRead:
    return catalog.update_episode(episode_id, data)


@router.delete("/episodes/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(episode_id: int, catalog: AdminCatalogServiceDep) -> None:
    catalog.delete_episode(episode_id)
