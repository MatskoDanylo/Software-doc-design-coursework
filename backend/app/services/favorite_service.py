from collections.abc import Sequence

from app.core.errors import NotFoundError
from app.models import Title, User
from app.schemas.catalog import TitlePage, TitleRead
from app.services.ports import EntityStore, FavoriteReader, FavoriteStore


def mark_favorites[T: TitleRead](items: Sequence[T], favorites: FavoriteReader, viewer_id: int | None) -> list[T]:
    if viewer_id is None:
        return list(items)
    ids = favorites.favorite_ids(viewer_id, {item.id for item in items})
    return [item.model_copy(update={"is_favorite": item.id in ids}) for item in items]


class FavoriteService:
    def __init__(self, favorites: FavoriteStore, titles: EntityStore[Title]) -> None:
        self.favorites = favorites
        self.titles = titles

    def add(self, user: User, title_id: int) -> None:
        if self.titles.get(title_id) is None:
            raise NotFoundError("Title not found", code="title_not_found")
        self.favorites.add(user.id, title_id)

    def remove(self, user: User, title_id: int) -> None:
        self.favorites.remove(user.id, title_id)

    def list(self, user: User, page: int, page_size: int) -> TitlePage:
        items, total = self.favorites.page(user.id, page, page_size)
        return TitlePage(
            items=[TitleRead.model_validate(t).model_copy(update={"is_favorite": True}) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )
