from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mealprep"

    # Supabase project URL, e.g. https://abcd1234.supabase.co
    supabase_url: str = ""
    # Server-only key, used to delete a user's Supabase account. Never ship it to the app.
    supabase_service_role_key: str = ""
    # The `aud` claim Supabase puts on signed-in users' access tokens.
    supabase_jwt_audience: str = "authenticated"


@lru_cache
def get_settings() -> Settings:
    return Settings()
