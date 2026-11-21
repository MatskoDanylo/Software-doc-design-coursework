from sqlalchemy import select

from app.models import User
from app.repositories.base import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))
