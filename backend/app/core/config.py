from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    # Railway injects DATABASE_URL; individual vars are used for local dev
    db_url: str = Field(default="", alias="DATABASE_URL")
    postgres_user: str = "convexity"
    postgres_password: str = "convexity_secret"
    postgres_db: str = "convexityedge"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        if self.db_url:
            url = self.db_url
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        if self.db_url:
            url = self.db_url
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ─────────────────────────────────────────────────────────────────
    # Railway injects REDIS_URL; individual vars are used for local dev
    cache_url: str = Field(default="", alias="REDIS_URL")
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        if self.cache_url:
            return self.cache_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    secret_key: str = "change_me_in_production"
    # Comma-separated string of allowed CORS origins
    cors_origins_str: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> list:
        return [o.strip() for o in self.cors_origins_str.split(",") if o.strip()]

    # ── Market Data ───────────────────────────────────────────────────────────
    market_data_provider: str = "yfinance"
    chain_refresh_interval: int = 60

    # ── Angel One SmartAPI (only needed when MARKET_DATA_PROVIDER=angel_one) ─
    angel_one_api_key:     str = ""
    angel_one_client_code: str = ""
    angel_one_password:    str = ""
    angel_one_totp_secret: str = ""

    # ── Quant Engine ─────────────────────────────────────────────────────────
    risk_free_rate: float = 0.065   # RBI repo rate
    iv_solver_max_iterations: int = 100
    iv_solver_tolerance: float = 1e-6
    cache_ttl: int = 90


settings = Settings()
