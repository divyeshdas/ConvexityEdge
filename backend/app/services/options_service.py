"""
Options chain service: fetches, enriches, and caches option chain data.
"""

import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.redis import cache_get, cache_set, make_cache_key
from app.models.symbol import Symbol
from app.models.option_contract import OptionContract
from app.models.chain_snapshot import OptionChainSnapshot
from data.pipeline import get_provider, enrich_chain, watch_symbol


async def get_option_chain(
    symbol: str,
    expiry_str: str,
    strikes: int = 30,
) -> Optional[dict]:
    """
    Fetch, enrich, and return option chain. Checks Redis cache first.
    """
    symbol = symbol.upper()
    cache_key = make_cache_key("chain", symbol=symbol, expiry=expiry_str, strikes=strikes)

    cached = await cache_get(cache_key)
    if cached:
        return cached

    watch_symbol(symbol)
    provider = get_provider()

    try:
        expiry = datetime.date.fromisoformat(expiry_str)
    except ValueError:
        return None

    import asyncio as _aio
    # Fetch quote, chain, and close prices in parallel — saves ~2-3s per request
    quote, contracts, close_prices = await _aio.gather(
        provider.get_quote(symbol),
        provider.get_option_chain(symbol, expiry),
        provider.get_close_prices(symbol, days=60),
    )
    enriched  = enrich_chain(contracts, quote.price, settings.risk_free_rate, 0.0)

    dte = (expiry - datetime.date.today()).days

    # Build strike-centered structure
    calls = {c["strike"]: c for c in enriched if c["option_type"] == "C"}
    puts  = {c["strike"]: c for c in enriched if c["option_type"] == "P"}

    all_strikes = sorted(set(list(calls.keys()) + list(puts.keys())))

    # Center around ATM, take ±strikes/2 strikes
    if all_strikes:
        atm = min(all_strikes, key=lambda k: abs(k - quote.price))
        atm_idx = all_strikes.index(atm)
        half = strikes // 2
        lo = max(0, atm_idx - half)
        hi = min(len(all_strikes), atm_idx + half)
        selected_strikes = all_strikes[lo:hi]
    else:
        selected_strikes = all_strikes

    chain_strikes = []
    for K in selected_strikes:
        call = _leg_dict(calls.get(K))
        put  = _leg_dict(puts.get(K))
        chain_strikes.append({
            "strike": K,
            "call":   call,
            "put":    put,
            "is_atm": abs(K - quote.price) == min(abs(s - quote.price) for s in selected_strikes),
        })

    # Stats
    total_call_vol = sum(c["volume"] or 0 for c in enriched if c["option_type"] == "C")
    total_put_vol  = sum(c["volume"] or 0 for c in enriched if c["option_type"] == "P")
    total_call_oi  = sum(c["open_interest"] or 0 for c in enriched if c["option_type"] == "C")
    total_put_oi   = sum(c["open_interest"] or 0 for c in enriched if c["option_type"] == "P")

    all_ivs = [c["implied_vol"] for c in enriched if c["implied_vol"]]
    atm_iv  = None
    if all_ivs:
        atm_contracts = [(c["strike"], c["implied_vol"]) for c in enriched if c["implied_vol"]]
        if atm_contracts:
            _, atm_iv = min(atm_contracts, key=lambda x: abs(x[0] - quote.price))

    iv_changes = [c["iv_change_1d"] for c in enriched if c.get("iv_change_1d") is not None]

    from quant_engine.iv_surface import compute_historical_vol
    hist_vol = compute_historical_vol(close_prices, window=30)

    chain_data = {
        "symbol":     symbol,
        "expiry":     expiry_str,
        "dte":        dte,
        "underlying": round(quote.price, 4),
        "strikes":    chain_strikes,
        "stats": {
            "atm_iv":          atm_iv,
            "hist_vol_30d":    hist_vol,
            "pcr_volume":      round(total_put_vol / total_call_vol, 4) if total_call_vol else 0.0,
            "pcr_oi":          round(total_put_oi / total_call_oi, 4) if total_call_oi else 0.0,
            "total_call_vol":  total_call_vol,
            "total_put_vol":   total_put_vol,
            "total_call_oi":   total_call_oi,
            "total_put_oi":    total_put_oi,
            "iv_change_avg":   round(sum(iv_changes) / len(iv_changes), 6) if iv_changes else None,
        },
        "fetched_at": datetime.datetime.utcnow().isoformat(),
    }

    await cache_set(cache_key, chain_data, ttl=settings.cache_ttl)
    return chain_data


def _leg_dict(contract: Optional[dict]) -> Optional[dict]:
    if contract is None:
        return None
    return {
        "option_type":   contract["option_type"],
        "strike":        contract["strike"],
        "expiry":        contract["expiry"],
        "bid":           contract["bid"],
        "ask":           contract["ask"],
        "last":          contract["last"],
        "volume":        contract["volume"],
        "open_interest": contract["open_interest"],
        "implied_vol":   contract["implied_vol"],
        "iv_change_1d":  contract["iv_change_1d"],
        "greeks":        contract["greeks"],
        "in_the_money":  contract["in_the_money"],
    }


async def get_expiries(symbol: str) -> list[dict]:
    symbol = symbol.upper()
    cache_key = make_cache_key("expiries", symbol=symbol)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    provider = get_provider()
    raw_expiries = await provider.get_expiries(symbol)
    today = datetime.date.today()

    result = []
    for d in raw_expiries:
        dte = (d - today).days
        if dte < 0:
            continue
        label = f"{d.strftime('%b %d \'%y')} · {dte}d"
        result.append({"date": d.isoformat(), "dte": dte, "label": label})

    await cache_set(cache_key, result, ttl=300)  # cache expiry list for 5 min
    return result


async def store_chain_snapshot(db: AsyncSession, symbol: str, expiry, enriched: list, underlying: float):
    """Persist a chain snapshot to PostgreSQL for historical IV analytics."""
    # Upsert symbol
    stmt = select(Symbol).where(Symbol.ticker == symbol)
    result = await db.execute(stmt)
    sym = result.scalar_one_or_none()
    if not sym:
        sym = Symbol(ticker=symbol, name=symbol, exchange="UNKNOWN", asset_type="equity")
        db.add(sym)
        await db.flush()

    for c in enriched:
        # Upsert contract
        stmt = select(OptionContract).where(
            OptionContract.symbol_id   == sym.id,
            OptionContract.option_type == c["option_type"],
            OptionContract.strike      == c["strike"],
            OptionContract.expiry      == expiry,
        )
        res = await db.execute(stmt)
        contract = res.scalar_one_or_none()
        if not contract:
            contract = OptionContract(
                symbol_id=sym.id,
                option_type=c["option_type"],
                strike=c["strike"],
                expiry=expiry,
            )
            db.add(contract)
            await db.flush()

        snapshot = OptionChainSnapshot(
            contract_id=contract.id,
            underlying_price=underlying,
            bid=c["bid"],
            ask=c["ask"],
            last_price=c["last"],
            volume=c["volume"],
            open_interest=c["open_interest"],
            implied_vol=c["implied_vol"],
            delta=c["greeks"]["delta"] if c["greeks"] else None,
            gamma=c["greeks"]["gamma"] if c["greeks"] else None,
            vega=c["greeks"]["vega"]   if c["greeks"] else None,
            theta=c["greeks"]["theta"] if c["greeks"] else None,
            rho=c["greeks"]["rho"]     if c["greeks"] else None,
        )
        db.add(snapshot)
