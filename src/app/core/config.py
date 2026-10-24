import os
from functools import lru_cache
from typing import Literal, Type

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )

    env: str = Field('development', env='APP_ENV')
    debug: bool = Field(False, env="DEBUG")
    database_url: str = Field(..., env="DATABASE_URL")
    schedule_slot_gap_minutes: int = Field(default=120, ge=0, le=24 * 60)
    session_timeout_minutes: int = Field(default=15, ge=1)
    session_duration_minutes: int = Field(default=15, ge=1)
    chat_message_retention_days: int = Field(default=7, ge=1)
    word_add_batch_retention_hours: int = Field(default=1, ge=1)

    # RabbitMQ
    rabbitmq_url: str = Field(..., env="RABBITMQ_URL")

    # LLM
    llm_provider: Literal["ollama", "gemini"] = "ollama"
    llm_base_url: str = "http://ollama:11434"
    llm_model: str = "qwen3:4b"
    llm_timeout_seconds: float = 120
    llm_temperature: float = 0
    llm_context_size: int = 4096
    llm_rate_limit_retries: int = Field(default=5, ge=0)
    llm_rate_limit_max_delay_seconds: float = Field(default=10, ge=1)
    gemini_api_key: str = ""

    # Telegram
    telegram_api_uri: str = Field(
        default="https://api.telegram.org",
        env="TELEGRAM_API_URI"
    )
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_bot_url: str = Field(..., env="TELEGRAM_BOT_URL")
    contact_telegram_username: str = Field(..., env="CONTACT_TELEGRAM_USERNAME")
    contact_email: str = Field(..., env="CONTACT_EMAIL")

    @model_validator(mode="after")
    def require_gemini_api_key(self) -> "AppSettings":
        if self.llm_provider == "gemini" and not self.gemini_api_key.strip():
            raise ValueError("Для провайдера gemini нужен gemini_api_key")
        return self

class DevelopmentSettings(AppSettings):
    debug: bool = True

class TestingSettings(AppSettings):
    debug: bool = True
    env: str = 'testing'
    test_database_url: str

    @model_validator(mode="after")
    def apply_test_database(self) -> "TestingSettings":
        self.database_url = self.test_database_url
        return self

class ProductionSettings(AppSettings):
    debug: bool = False
    https: bool = True

_ENV_TO_CLASS: dict[str, Type[AppSettings]] = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings
}

@lru_cache
def get_config() -> AppSettings:
    if "APP_ENV" not in os.environ:
        load_dotenv()

    env: str = os.getenv("APP_ENV", "development").strip().lower()
    SettingsClass = _ENV_TO_CLASS.get(env, DevelopmentSettings)
    return SettingsClass(env=env)
