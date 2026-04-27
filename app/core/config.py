from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    
    DATA_DIR: Path = Path("/opt/airflow/data")
    database_url: str = "postgresql+psycopg://scope:scope@postgres:5432/scope"
    SHEET_NAME: str = "MASTER"

    cors_allow_origins: list[str] = ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Cached singleton for modules that expect `settings` (e.g. Airflow DAGs).
settings: Settings = get_settings()
