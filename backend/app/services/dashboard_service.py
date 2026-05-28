import asyncio
import datetime
from app.core.redis import cache_get, cache_set, make_cache_key
from app.core.config import settings
from data.pipeline import get_provider, enrich_chain
from quant_engine.iv_surface import compute_historical_vol
from analytics.dashboard_analytics import compute_dashboard_analytics


async def get_dashboard_analytics(symbol: str) -> dict:
    cache_key = make_cache_key("dashboard", symbol=symbol)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    provider = get_provider()

    # Fetch quote and expiries in parallel
    quote, expiries = await asyncio.gather(
        provider.get_quote(symbol),
        provider.get_expiries(symbol),
    )

    if not expiries:
        return {}

    today  = datetime.date.today()
    expiry = min(expiries, key=lambda e: (e - today).days if (e - today).days > 0 else 999)

    # Fetch option chain and historical prices in parallel
    contracts, close_prices = await asyncio.gather(
        provider.get_option_chain(symbol, expiry),
        provider.get_close_prices(symbol, days=60),
    )

    enriched = enrich_chain(contracts, quote.price, settings.risk_free_rate, 0.0)
    hist_vol = compute_historical_vol(close_prices, window=30)

    result = compute_dashboard_analytics(enriched, quote.price, hist_vol=hist_vol)
    result["symbol"]     = symbol.upper()
    result["underlying"] = round(quote.price, 4)
    result["expiry"]     = expiry.isoformat()

    await cache_set(cache_key, result, ttl=settings.cache_ttl)
    return result
