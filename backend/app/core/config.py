from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cinema:cinema@localhost:5432/cinema"
    secret_key: str = "dev-secret"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    media_dir: str = "../media"
    premium_days: int = 30


settings = Settings()
