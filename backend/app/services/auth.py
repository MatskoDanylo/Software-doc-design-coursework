from app.core.errors import UnauthorizedError
from app.core.security import TokenType, create_token, decode_token, verify_password
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair
from app.services.users import UserService


class AuthService:
    def __init__(self, users: UserRepository, user_service: UserService) -> None:
        self.users = users
        self.user_service = user_service

    def register(self, data: RegisterRequest) -> User:
        return self.user_service.create(data.email, data.password, data.display_name)

    def login(self, data: LoginRequest) -> TokenPair:
        user = self.users.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password", code="invalid_credentials")
        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        return self._issue_tokens(self._user_from_token(refresh_token, TokenType.REFRESH))

    def authenticate(self, access_token: str) -> User:
        return self._user_from_token(access_token, TokenType.ACCESS)

    def _user_from_token(self, token: str, token_type: TokenType) -> User:
        user = self.users.get(decode_token(token, token_type))
        if user is None:
            raise UnauthorizedError("User no longer exists", code="invalid_token")
        return user

    @staticmethod
    def _issue_tokens(user: User) -> TokenPair:
        return TokenPair(
            access_token=create_token(user.id, TokenType.ACCESS),
            refresh_token=create_token(user.id, TokenType.REFRESH),
        )
