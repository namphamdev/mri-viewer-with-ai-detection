"""Application configuration via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Local image storage
    images_dir: str = str(Path(__file__).resolve().parent.parent / "data" / "images")

    # PACS server configuration (legacy, kept for reference)
    pacs_base_url: str = "https://pacs.mids.com.vn/pacs/rs"
    pacs_timeout: int = 30  # seconds

    # PACS authentication
    pacs_access_key: str = "U3k-m5Ld5Jvvrr1pZqmFZcZzUy1oYXTOht6hF7WcB2A="

    # Default study/series for development
    default_study_uid: str = "1.2.840.113619.2.182.108086160931.1772161975.1903259"
    default_series_uid: str = (
        "1.2.392.200036.9123.100.12.12.40828.90260227102559140408022612"
    )

    # CORS origins
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "MRI_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
