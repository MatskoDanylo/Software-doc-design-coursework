from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Season, Title
from app.patterns.title_query_builder import TitleQuery
from app.repositories.base import SqlAlchemyRepository


class TitleRepository(SqlAlchemyRepository[Title]):
    model = Title

    def search(self, query: TitleQuery) -> tuple[Sequence[Title], int]:
        total = self.session.scalar(query.count) or 0
        return self.session.scalars(query.items).all(), total

    def get_detailed(self, title_id: int) -> Title | None:
        return self.session.scalar(
            select(Title)
            .where(Title.id == title_id)
            .options(selectinload(Title.seasons).selectinload(Season.episodes))
        )

    def list_countries(self) -> list[str]:
        return list(self.session.scalars(select(Title.country).distinct().order_by(Title.country)))
