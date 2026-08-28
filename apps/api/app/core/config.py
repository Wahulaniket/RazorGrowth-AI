from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RazorGrowth AI API"
    app_env: str = "development"
    debug: bool = True

    database_url: str
    redis_url: str

    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # LLM Provider
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_provider: str = "openai"  # "openai" | "fake"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()