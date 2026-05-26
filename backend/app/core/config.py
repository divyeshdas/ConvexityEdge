from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    postgres_user: str = "convexity"
    postgres_password: str = "convexity_secret"
    postgres_db: str = "convexityedge"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    secret_key: str = "change_me_in_production"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Market Data ───────────────────────────────────────────────────────────
    market_data_provider: str = "yfinance"
    chain_refresh_interval: int = 60

    # ── Quant Engine ─────────────────────────────────────────────────────────
    risk_free_rate: float = 0.0525
    iv_solver_max_iterations: int = 100
    iv_solver_tolerance: float = 1e-6
    cache_ttl: int = 60


settings = Settings()
