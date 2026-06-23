from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    ingest_initial_window_hours: int = 336
    ingest_sync_window_hours: int = 168
    ingest_subscription_id: str | None = None
    transcript_languages: list[str] = ["en", "nl"]
    exclude_shorts: bool = True

    openai_api_key: str | None = None
    openai_simple_model: str = "gpt-5.4-nano"
    openai_model: str = "gpt-5.4-mini"
    enrichment_transcript_max_seconds: int = 900
    enrichment_window_hours: int | None = None

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
