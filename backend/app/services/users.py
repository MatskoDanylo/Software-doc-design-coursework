from collections.abc import Sequence

from app.core.errors import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import Profile, Role, User
from app.repositories.users import UserRepository
from app.schemas.common import normalize_email
from app.schemas.user import ProfileUpdate


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def create(self, email: str, password: str, display_name: str | None = None, role: Role = Role.USER) -> User:
        email = normalize_email(email)
        if self.users.get_by_email(email) is not None:
            raise ConflictError("Email is already registered", code="email_taken")
        return self.users.add(User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            profile=Profile(display_name=display_name or email.split("@")[0]),
        ))

    def get(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found", code="user_not_found")
        return user

    def update_profile(self, user: User, data: ProfileUpdate) -> User:
        for field, value in data.model_dump(mode="json", exclude_unset=True).items():
            setattr(user.profile, field, value)
        return user

    def list_users(self, limit: int, offset: int) -> Sequence[User]:
        return self.users.get_page(limit, offset)
