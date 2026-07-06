from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Football AI Analyst"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"
    api_v1_prefix: str = "/api/v1"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "football_ai"
    postgres_password: str = "football_ai_secret"
    postgres_db: str = "football_ai"
    database_url: str = "postgresql+asyncpg://football_ai:football_ai_secret@localhost:5432/football_ai"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    the_odds_api_key: str = ""
    the_odds_api_base_url: str = "https://api.the-odds-api.com/v4"

    mlflow_tracking_uri: str = "http://localhost:5000"
    model_registry_path: str = "./ml/artifacts"

    training_season: int = 2024
    training_max_pages: int = 3

    rate_limit_per_minute: int = 60

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:80"]

    @field_validator("api_football_key", "the_odds_api_key", mode="before")
    @classmethod
    def strip_api_keys(cls, value: object) -> str:
        if value is None:
            return ""
        cleaned = str(value).strip().strip('"').strip("'")
        return cleaned


@lru_cache
def get_settings() -> Settings:
    return Settings()
