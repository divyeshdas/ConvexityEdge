from fastapi import APIRouter
from app.api.v1.routes import (
    symbols, market, options, pricing, greeks, iv, strategy, trade, dashboard
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(symbols.router)
api_router.include_router(market.router)
api_router.include_router(options.router)
api_router.include_router(pricing.router)
api_router.include_router(greeks.router)
api_router.include_router(iv.router)
api_router.include_router(strategy.router)
api_router.include_router(trade.router)
api_router.include_router(dashboard.router)
