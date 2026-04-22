# app/config.py
"""
Application configuration using Pydantic Settings.
Validates all environment variables at startup — fails fast if misconfigured.
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


# Trỏ tuyệt đối tới .env ở THƯ MỤC GỐC PROJECT (cùng cấp main.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Centralized configuration with type validation.
    All values loaded from .env file or environment variables.
    """

    # ── Database ──
    user: str
    password: str
    host: str
    port: int = 5432
    dbname: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.dbname}?sslmode=require"
        )

    # ── Auth ──
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── LLM ──
    OPENROUTER_API_KEY: str
    LLM_MODEL: str = "deepseek/deepseek-chat-v3.1:free"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # ── RAG ──
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5

    # ── Paths ──
    JSON_URL: str = ""
    VECTOR_STORE_PATH: str = str(PROJECT_ROOT / "app" / "vector_stores")

    # ── App Meta ──
    APP_NAME: str = "VietCare Assistant"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # ── Conversation ──
    MAX_HISTORY_MESSAGES: int = 10

    model_config = {
        "env_file": str(ENV_PATH),
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # ignore extra env vars
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — only parsed once."""
    return Settings()


# Backward-compatible alias
config = get_settings()
