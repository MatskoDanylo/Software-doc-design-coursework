from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CatalogServiceDep, OptionalUser
from app.schemas.catalog import GenreRead, TitleDetail, TitleFilters, TitlePage

router = APIRouter(tags=["catalog"])


@router.get("/titles")
def search_titles(
    filters: Annotated[TitleFilters, Query()], catalog: CatalogServiceDep, user: OptionalUser
) -> TitlePage:
    return catalog.search(filters, user.id if user else None)


@router.get("/titles/{title_id}")
def get_title(title_id: int, catalog: CatalogServiceDep, user: OptionalUser) -> TitleDetail:
    return catalog.get_title(title_id, user.id if user else None)


@router.get("/genres", response_model=list[GenreRead])
def list_genres(catalog: CatalogServiceDep) -> object:
    return catalog.list_genres()


@router.get("/countries")
def list_countries(catalog: CatalogServiceDep) -> list[str]:
    return catalog.list_countries()
