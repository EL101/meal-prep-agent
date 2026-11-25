from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    # Postgres (Supabase-hosted in prod, docker-compose locally). Must use the asyncpg driver.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mealprep"
    redis_url: str = "redis://localhost:6379"

    # Supabase: JWT secret verifies the mobile app's access tokens; service key is server-only.
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_storage_bucket: str = "inventory-images"

    # Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-5-5"
    claude_effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"

    # External data sources
    usda_api_key: str = ""
    kroger_client_id: str = ""
    kroger_client_secret: str = ""
    bls_api_key: str = ""

    cors_origins: list[str] = ["http://localhost:8081"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
