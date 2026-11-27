from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/mealprep"

    # Supabase project URL, e.g. https://abcd1234.supabase.co
    supabase_url: str = ""
    # Supabase secret key (sb_secret_...), used to delete a user's Supabase account.
    # Server-only: never ship it to the app.
    supabase_secret_key: str = ""
    # The `aud` claim Supabase puts on signed-in users' access tokens.
    supabase_jwt_audience: str = "authenticated"

    # Browser origins allowed to call the API (the Expo web build). Native apps don't send an
    # Origin, so they aren't affected. Set as a JSON list, e.g. CORS_ORIGINS='["https://app.example"]'.
    cors_origins: list[str] = ["http://localhost:8081"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
