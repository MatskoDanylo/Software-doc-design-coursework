from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Season, Title, TitleKind
from app.patterns.title_query_builder import TitleQuery
from app.repositories.base import SqlAlchemyRepository


class TitleRepository(SqlAlchemyRepository[Title]):
    model = Title

    def search(self, query: TitleQuery) -> tuple[Sequence[Title], int]:
        total = self.session.scalar(query.count) or 0
        return self.session.scalars(query.items).all(), total

    def get_detailed(self, title_id: int) -> Title | None:
        return self.session.scalar(
            select(Title).where(Title.id == title_id).options(selectinload(Title.seasons).selectinload(Season.episodes))
        )

    def get_many(self, title_ids: Sequence[int]) -> list[Title]:
        if not title_ids:
            return []
        found = {t.id: t for t in self.session.scalars(select(Title).where(Title.id.in_(list(title_ids))))}
        return [found[i] for i in title_ids if i in found]

    def get_by_identity(self, kind: TitleKind, name: str, year: int) -> Title | None:
        return self.session.scalar(
            select(Title).where(Title.kind == kind.value, Title.name == name, Title.year == year)
        )

    def list_countries(self) -> list[str]:
        return list(self.session.scalars(select(Title.country).distinct().order_by(Title.country)))

    def list_movies(self, limit: int) -> Sequence[Title]:
        return self.session.scalars(
            select(Title).where(Title.kind == TitleKind.MOVIE.value).order_by(Title.id).limit(limit)
        ).all()
