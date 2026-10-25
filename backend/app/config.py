"""Application configuration using Pydantic Settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RE-THREAD"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Database: SQLite by default for zero-config local development and testing,
    # swappable to PostgreSQL via env var (e.g. postgresql://postgres:postgres@localhost:5432/rethread_db)
    DATABASE_URL: str = "sqlite:///./rethread.db"

    # ML & Decision Engine Configuration
    CONFIDENCE_THRESHOLD: float = 0.60
    DEFAULT_GARMENT_WEIGHT_KG: float = 0.30
    RANKER_TYPE: str = "xgboost"  # Options: 'xgboost' (Phase 7) or 'formula' (Phase 3)

    # Default Pune coordinates (FC Road / Central Pune)
    DEFAULT_PUNE_LATITUDE: float = 18.5204
    DEFAULT_PUNE_LONGITUDE: float = 73.8567

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
