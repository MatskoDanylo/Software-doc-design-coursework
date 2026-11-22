from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CatalogServiceDep
from app.schemas.catalog import GenreRead, TitleDetail, TitleFilters, TitlePage

router = APIRouter(tags=["catalog"])


@router.get("/titles")
def search_titles(filters: Annotated[TitleFilters, Query()], catalog: CatalogServiceDep) -> TitlePage:
    return catalog.search(filters)


@router.get("/titles/{title_id}", response_model=TitleDetail)
def get_title(title_id: int, catalog: CatalogServiceDep) -> object:
    return catalog.get_title(title_id)


@router.get("/genres", response_model=list[GenreRead])
def list_genres(catalog: CatalogServiceDep) -> object:
    return catalog.list_genres()


@router.get("/countries")
def list_countries(catalog: CatalogServiceDep) -> list[str]:
    return catalog.list_countries()
