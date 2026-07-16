"""
Centralized application configuration.

All values are overridable via environment variables or a `.env` file.
Nothing secret is hard-coded here - see `.env.example` at the repo root.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Agentic Financial Advisor"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Security / Auth ---
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"  # set via env var in real deployments
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://findadvisor:findadvisor@localhost:5432/findadvisor"
    )

    # --- Groq (free tier, no credit card, no billing/prepay system) ---
    GROQ_API_KEY: str = ""
    GROQ_CHAT_MODEL: str = "llama-3.1-8b-instant"
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT_SECONDS: int = 30

    # --- Embeddings: run locally via fastembed, no API key/quota/billing ever ---
    FASTEMBED_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
    FASTEMBED_CACHE_PATH: str = ""  # empty = fastembed's own default cache location

    # --- RAG ---
    RAG_TOP_K: int = 4
    EMBEDDING_DIM: int = 768  # matches BAAI/bge-base-en-v1.5's native output size

    # --- Observability ---
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # empty disables OTLP export, console fallback used
    ENABLE_PROMETHEUS: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
