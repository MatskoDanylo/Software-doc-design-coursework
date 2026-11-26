from collections.abc import Iterable, Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Favorite, Title


class FavoriteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, user_id: int, title_id: int) -> None:
        self.session.execute(insert(Favorite).values(user_id=user_id, title_id=title_id).on_conflict_do_nothing())

    def remove(self, user_id: int, title_id: int) -> None:
        self.session.execute(delete(Favorite).where(Favorite.user_id == user_id, Favorite.title_id == title_id))

    def page(self, user_id: int, page: int, page_size: int) -> tuple[Sequence[Title], int]:
        total = self.session.scalar(select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id))
        items = self.session.scalars(
            select(Title)
            .join(Favorite, Favorite.title_id == Title.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.added_at.desc(), Title.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
        return items, total or 0

    def favorite_ids(self, user_id: int, title_ids: Iterable[int]) -> set[int]:
        ids = list(title_ids)
        if not ids:
            return set()
        return set(
            self.session.scalars(
                select(Favorite.title_id).where(Favorite.user_id == user_id, Favorite.title_id.in_(ids))
            )
        )
