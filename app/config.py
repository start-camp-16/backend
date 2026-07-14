from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mwohalgu.db"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.4-mini"
    chat_location_limit: int = Field(default=5, ge=1, le=20)
    chat_post_limit: int = Field(default=5, ge=1, le=20)
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
