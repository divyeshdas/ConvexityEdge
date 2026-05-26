import time
from app.core.redis import cache_get, cache_set, make_cache_key
from app.core.config import settings
from quant_engine.black_scholes import bs_price_with_decomposition, bs_price_batch
from quant_engine.greeks import greeks_scalar, greeks_batch


async def price_single(S, K, T, r, q, sigma, option_type) -> dict:
    cache_key = make_cache_key("bs", S=S, K=K, T=T, r=r, q=q, sigma=sigma, t=option_type)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = bs_price_with_decomposition(S, K, T, r, q, sigma, option_type)
    greeks = greeks_scalar(S, K, T, r, q, sigma, option_type)
    result["greeks"] = greeks

    await cache_set(cache_key, result, ttl=settings.cache_ttl)
    return result


async def price_batch(contracts: list[dict]) -> dict:
    t0 = time.perf_counter()
    prices = bs_price_batch(contracts)
    elapsed = (time.perf_counter() - t0) * 1000
    return {"prices": prices, "count": len(prices), "elapsed_ms": round(elapsed, 2)}
