import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import orjson
from fastapi.responses import ORJSONResponse, JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.redis import close_redis
from app.api.v1.router import api_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("convexityedge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ConvexityEdge backend starting...")

    from app.core.database import AsyncSessionLocal
    from app.core.redis import get_redis
    from data.pipeline import get_provider, run_refresh_loop

    # Pre-warm: kick off instrument download + auth in background so first
    # user request doesn't have to wait for either.
    async def _prewarm():
        try:
            provider = get_provider()
            await asyncio.gather(
                provider._ensure_instruments(),
                provider._ensure_auth(),
                return_exceptions=True,
            )
            logger.info("Provider pre-warm complete")
        except Exception as exc:
            logger.warning("Provider pre-warm failed (non-fatal): %s", exc)

    asyncio.create_task(_prewarm())

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


class _CatchAllMiddleware:
    """Pure ASGI middleware — placed inside CORSMiddleware so 500 responses get CORS headers."""
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            logger.exception("Unhandled exception: %s", exc)
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
            await response(scope, receive, send)


app = FastAPI(
    title="ConvexityEdge",
    description="Professional Black-Scholes Options Volatility Analytics Platform",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# _CatchAllMiddleware added first → ends up inside CORSMiddleware in the ASGI stack.
# This ensures 500 error responses flow through CORSMiddleware and get CORS headers.
app.add_middleware(_CatchAllMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "convexityedge"}
