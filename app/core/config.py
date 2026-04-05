from pathlib import Path
from functools import lru_cache
from pydantic import Field
from typing import List
from pydantic_settings import SettingsConfigDict, BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env",
        ),
        case_sensitive=False,
        extra="ignore",
    )
    # POSTGRES
    database_url: str
    db_echo: bool = False
    db_echo_pool: bool = False
    db_pool_size: int
    db_max_overflow: int
    db_pool_pre_ping: bool
    db_pool_recycle: int
    db_create_retries: int
    db_create_retry_delay: int
    allow_db_create: int = 0
    postgres_maintenance_db: str


class RunModel(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8012


class ApiV1Prefix(BaseSettings):
    prefix: str = "/v1"


class ApiPrefix(BaseSettings):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env",
        ),
        case_sensitive=False,
        extra="ignore",
    )
    # BACKEND
    debug: bool = False
    secret_key: str
    allowed_hosts: List[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])

    db: DatabaseSettings = DatabaseSettings()
    run: RunModel = RunModel()
    api: ApiPrefix = ApiPrefix()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()