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
    backend_cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://localhost:8081",

    ]

    # LLM Provider
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_provider: str = "openai"  # "openai" | "fake"

    # Payment Provider
    payment_provider: str = "fake"  # "fake" | "razorpay"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    def validate_production(self):
        if self.app_env == "production":
            if not self.razorpay_key_id or self.razorpay_key_id in ["", "CHANGE_ME", "test"]:
                raise ValueError("Valid RAZORPAY_KEY_ID is required in production")
            if not self.razorpay_key_secret or self.razorpay_key_secret in ["", "CHANGE_ME", "test"]:
                raise ValueError("Valid RAZORPAY_KEY_SECRET is required in production")
            if not self.razorpay_webhook_secret or self.razorpay_webhook_secret in ["", "CHANGE_ME", "test"]:
                raise ValueError("Valid RAZORPAY_WEBHOOK_SECRET is required in production")
            if self.jwt_secret_key in ["", "CHANGE_ME", "secret", "test-secret"]:
                raise ValueError("Valid JWT_SECRET_KEY is required in production")

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings
