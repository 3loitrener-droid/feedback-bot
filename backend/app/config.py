from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://feedback:feedback_secret@localhost:5432/feedback_bot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""

    # LLM — выбор провайдера: "anthropic" или "groq"
    llm_provider: str = "groq"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Auth
    secret_key: str = "change_me_in_production_at_least_32_characters_long"
    magic_link_expire_minutes: int = 30
    session_expire_hours: int = 8

    # App
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    environment: str = "development"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@company.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
