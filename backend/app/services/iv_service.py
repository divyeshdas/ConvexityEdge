import datetime
from app.core.redis import cache_get, cache_set, make_cache_key
from app.core.config import settings
from data.pipeline import get_provider, enrich_chain
from quant_engine.iv_solver import solve_iv
from quant_engine.iv_surface import (
    build_iv_smile, build_iv_skew,
    build_iv_term_structure, build_iv_surface,
    compute_atm_iv,
)


async def solve_single_iv(market_price, S, K, T, r, q, option_type) -> dict:
    cache_key = make_cache_key("iv", mp=market_price, S=S, K=K, T=T, r=r, q=q, t=option_type)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = solve_iv(market_price, S, K, T, r, q, option_type)
    await cache_set(cache_key, result, ttl=settings.cache_ttl)
    return result


async def get_iv_smile(symbol: str, expiry_str: str) -> list[dict]:
    cache_key = make_cache_key("smile", symbol=symbol, expiry=expiry_str)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    provider = get_provider()
    quote    = await provider.get_quote(symbol)
    expiry   = datetime.date.fromisoformat(expiry_str)
    contracts = await provider.get_option_chain(symbol, expiry)
    enriched  = enrich_chain(contracts, quote.price, settings.risk_free_rate, 0.0)

    strikes  = [c["strike"]      for c in enriched if c["implied_vol"]]
    ivs      = [c["implied_vol"] for c in enriched if c["implied_vol"]]
    types    = [c["option_type"] for c in enriched if c["implied_vol"]]

    result = build_iv_smile(strikes, ivs, types, quote.price)
    await cache_set(cache_key, result, ttl=settings.cache_ttl)
    return result


async def get_iv_skew(symbol: str, expiry_str: str) -> list[dict]:
    cache_key = make_cache_key("skew", symbol=symbol, expiry=expiry_str)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    provider  = get_provider()
    quote     = await provider.get_quote(symbol)
    expiry    = datetime.date.fromisoformat(expiry_str)
    contracts = await provider.get_option_chain(symbol, expiry)
    enriched  = enrich_chain(contracts, quote.price, settings.risk_free_rate, 0.0)

    strikes = [c["strike"]      for c in enriched if c["implied_vol"]]
    ivs     = [c["implied_vol"] for c in enriched if c["implied_vol"]]
    types   = [c["option_type"] for c in enriched if c["implied_vol"]]

    result = build_iv_skew(strikes, ivs, types, quote.price)
    await cache_set(cache_key, result, ttl=settings.cache_ttl)
    return result


async def get_iv_term_structure(symbol: str) -> list[dict]:
    cache_key = make_cache_key("term", symbol=symbol)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    provider = get_provider()
    quote    = await provider.get_quote(symbol)
    expiries = await provider.get_expiries(symbol)
    today    = datetime.date.today()

    exp_strs, dtes, atm_ivs = [], [], []
    for exp in expiries[:12]:  # first 12 expiries
        dte = (exp - today).days
        if dte < 1:
            continue
        try:
            contracts = await provider.get_option_chain(symbol, exp)
            enriched  = enrich_chain(contracts, quote.price, settings.risk_free_rate, 0.0)
            strikes   = [c["strike"]      for c in enriched if c["implied_vol"]]
            ivs       = [c["implied_vol"] for c in enriched if c["implied_vol"]]
            atm       = compute_atm_iv(strikes, ivs, quote.price)
            if atm:
                exp_strs.append(exp.isoformat())
                dtes.append(dte)
                atm_ivs.append(atm)
        except Exception:
            continue

    result = build_iv_term_structure(exp_strs, dtes, atm_ivs)
    await cache_set(cache_key, result, ttl=300)
    return result


async def get_iv_surface(symbol: str) -> list[dict]:
    cache_key = make_cache_key("surface", symbol=symbol)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    provider = get_provider()
    quote    = await provider.get_quote(symbol)
    expiries = await provider.get_expiries(symbol)
    today    = datetime.date.today()

    all_strikes, all_dtes, all_ivs = [], [], []
    for exp in expiries[:8]:
        dte = (exp - today).days
        if dte < 1:
            continue
        try:
            contracts = await provider.get_option_chain(symbol, exp)
            enriched  = enrich_chain(contracts, quote.price, settings.risk_free_rate, 0.0)
            for c in enriched:
                if c["implied_vol"]:
                    all_strikes.append(c["strike"])
                    all_dtes.append(dte)
                    all_ivs.append(c["implied_vol"])
        except Exception:
            continue

    result = build_iv_surface(all_strikes, all_dtes, all_ivs, quote.price)
    await cache_set(cache_key, result, ttl=300)
    return result
