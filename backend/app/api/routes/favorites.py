from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, FavoriteServiceDep
from app.patterns.title_query_builder import TitleQueryBuilder
from app.schemas.catalog import TitlePage

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("")
def list_favorites(
    user: CurrentUser,
    favorites: FavoriteServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=TitleQueryBuilder.MAX_PAGE_SIZE)] = TitleQueryBuilder.DEFAULT_PAGE_SIZE,
) -> TitlePage:
    return favorites.list(user, page, page_size)


@router.post("/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_favorite(title_id: int, user: CurrentUser, favorites: FavoriteServiceDep) -> None:
    favorites.add(user, title_id)


@router.delete("/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(title_id: int, user: CurrentUser, favorites: FavoriteServiceDep) -> None:
    favorites.remove(user, title_id)
