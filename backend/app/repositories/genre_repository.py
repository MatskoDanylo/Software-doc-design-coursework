from collections.abc import Sequence

from sqlalchemy import func, select

from app.models import Genre
from app.repositories.base import SqlAlchemyRepository


class GenreRepository(SqlAlchemyRepository[Genre]):
    model = Genre

    def list_all(self) -> Sequence[Genre]:
        return self.session.scalars(select(Genre).order_by(func.lower(Genre.name))).all()
