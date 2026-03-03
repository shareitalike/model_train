from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Kaithi OCR System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "CHANGE-THIS-256-BIT-KEY-IN-PRODUCTION-NOW"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "postgresql+asyncpg://kaithi:kaithi123@postgres:5432/kaithi_db"
    DATABASE_SYNC_URL: str = "postgresql://kaithi:kaithi123@postgres:5432/kaithi_db"

    REDIS_URL: str = "redis://redis:6379/0"

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "kaithi-docs"
    MINIO_SECURE: bool = False

    MODEL_PATH: str = "/app/models/kaithi-trocr-finetuned"
    TROCR_BASE: str = "microsoft/trocr-base-handwritten"
    MAX_FILE_SIZE_MB: int = 50
    OCR_BATCH_SIZE: int = 8
    CONFIDENCE_THRESHOLD: float = 0.75
    OCR_DPI: int = 300

    DEVANAGARI_FONT: str = "/app/fonts/NotoSansDevanagari-Regular.ttf"
    DEVANAGARI_FONT_BOLD: str = "/app/fonts/NotoSansDevanagari-Bold.ttf"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
