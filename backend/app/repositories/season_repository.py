from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Episode, Season
from app.repositories.base import SqlAlchemyRepository


class SeasonRepository(SqlAlchemyRepository[Season]):
    model = Season

    def get_by_number(self, title_id: int, number: int) -> Season | None:
        return self.session.scalar(select(Season).where(Season.title_id == title_id, Season.number == number))


class EpisodeRepository(SqlAlchemyRepository[Episode]):
    model = Episode

    def get_by_number(self, season_id: int, number: int) -> Episode | None:
        return self.session.scalar(select(Episode).where(Episode.season_id == season_id, Episode.number == number))

    def list_first(self, limit: int) -> Sequence[Episode]:
        return self.session.scalars(
            select(Episode)
            .join(Season)
            .options(joinedload(Episode.season).joinedload(Season.title))
            .order_by(Season.title_id, Season.number, Episode.number)
            .limit(limit)
        ).all()
