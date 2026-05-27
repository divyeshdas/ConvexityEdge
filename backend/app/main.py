import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import orjson
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.core.redis import close_redis
from app.api.v1.router import api_router

# Read CORS origins directly from env to avoid pydantic-settings parsing issues
_cors_env = os.getenv("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] or settings.cors_origins

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("convexityedge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ConvexityEdge backend starting...")

    # Start background data refresh loop
    from app.core.database import AsyncSessionLocal
    from app.core.redis import get_redis
    from data.pipeline import run_refresh_loop

    try:
        redis = await get_redis()
    except Exception:
        redis = None
    refresh_task = asyncio.create_task(
        run_refresh_loop(AsyncSessionLocal, redis)
    )
    logger.info(f"Market data refresh loop started (interval: {settings.chain_refresh_interval}s)")

    yield

    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass

    await close_redis()
    logger.info("ConvexityEdge backend shutting down.")


app = FastAPI(
    title="ConvexityEdge",
    description="Professional Black-Scholes Options Volatility Analytics Platform",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "convexityedge"}
