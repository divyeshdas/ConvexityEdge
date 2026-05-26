"""
60-second async market data refresh pipeline.

Responsibilities:
- Provides the singleton data provider instance
- Fetches and enriches option chain data (runs IV solver + Greeks engine)
- Writes snapshots to PostgreSQL
- Coordinates with Redis cache TTL

The pipeline is started in FastAPI's lifespan event and runs as a background
asyncio task. Each tick fetches all actively watched symbols.
"""

import asyncio
import datetime
import logging
from typing import Optional

from app.core.config import settings
from data.providers.base import MarketDataProvider
from data.providers.yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)

# ── Provider registry ──────────────────────────────────────────────────────────
PROVIDER_MAP: dict[str, type[MarketDataProvider]] = {
    "yfinance": YFinanceProvider,
}

_provider_instance: Optional[MarketDataProvider] = None


def get_provider() -> MarketDataProvider:
    global _provider_instance
    if _provider_instance is None:
        cls = PROVIDER_MAP.get(settings.market_data_provider, YFinanceProvider)
        _provider_instance = cls()
    return _provider_instance


# ── Watched symbols (populated by API when users load chains) ─────────────────
_watched_symbols: set[str] = set()


def watch_symbol(symbol: str):
    _watched_symbols.add(symbol.upper())


def unwatch_symbol(symbol: str):
    _watched_symbols.discard(symbol.upper())


# ── Chain enrichment ───────────────────────────────────────────────────────────
def enrich_chain(
    contracts,
    underlying: float,
    r: float,
    q: float,
) -> list[dict]:
    """
    Take raw OptionContractData list, run IV solver + Greeks engine,
    and return a list of enriched contract dicts ready for the API layer.

    Vectorized where possible (Greeks batch), IV solved in a fast loop.
    """
    import numpy as np
    from quant_engine.iv_solver import solve_iv
    from quant_engine.greeks import calculate_greeks

    today = datetime.date.today()
    enriched = []

    S_arr, K_arr, T_arr, r_arr, q_arr, sig_arr, types_arr = [], [], [], [], [], [], []

    # First pass: solve IV for all contracts, collect params
    for c in contracts:
        dte = (c.expiry - today).days
        T   = max(dte / 365.0, 1e-10)
        mid_price = (c.bid + c.ask) / 2.0 if c.bid and c.ask else c.last

        # Use market-reported IV if available and reasonable; otherwise solve it
        if c.implied_vol and 0.001 < c.implied_vol < 10.0:
            iv = c.implied_vol
        elif mid_price and mid_price > 0:
            result = solve_iv(mid_price, underlying, c.strike, T, r, q, c.option_type)
            iv = result["iv"] if result["converged"] else c.implied_vol
        else:
            iv = None

        S_arr.append(underlying)
        K_arr.append(c.strike)
        T_arr.append(T)
        r_arr.append(r)
        q_arr.append(q)
        sig_arr.append(iv if iv else 0.25)
        types_arr.append(c.option_type)

        enriched.append({
            "symbol":        c.symbol,
            "option_type":   c.option_type,
            "strike":        c.strike,
            "expiry":        c.expiry.isoformat(),
            "bid":           round(c.bid, 4),
            "ask":           round(c.ask, 4),
            "last":          round(c.last, 4),
            "volume":        c.volume,
            "open_interest": c.open_interest,
            "implied_vol":   round(iv, 6) if iv else None,
            "iv_change_1d":  None,
            "in_the_money":  (c.strike < underlying) if c.option_type == 'C' else (c.strike > underlying),
            "greeks":        None,  # filled in below
        })

    if not enriched:
        return enriched

    # Second pass: batch Greeks for all contracts
    S_np    = np.array(S_arr,    dtype=float)
    K_np    = np.array(K_arr,    dtype=float)
    T_np    = np.array(T_arr,    dtype=float)
    r_np    = np.array(r_arr,    dtype=float)
    q_np    = np.array(q_arr,    dtype=float)
    sig_np  = np.array(sig_arr,  dtype=float)
    type_np = np.array(types_arr)

    g = calculate_greeks(S_np, K_np, T_np, r_np, q_np, sig_np, type_np)

    for i, contract in enumerate(enriched):
        contract["greeks"] = {
            "delta": round(float(g["delta"][i]), 4),
            "gamma": round(float(g["gamma"][i]), 6),
            "vega":  round(float(g["vega"][i]),  4),
            "theta": round(float(g["theta"][i]), 4),
            "rho":   round(float(g["rho"][i]),   4),
        }

    return enriched


# ── Background refresh loop ────────────────────────────────────────────────────
async def run_refresh_loop(db_session_factory, redis_client):
    """
    Runs forever. Every `chain_refresh_interval` seconds, for each watched
    symbol, fetches the chain and stores a snapshot to the DB + Redis.
    """
    from app.services.options_service import store_chain_snapshot

    while True:
        await asyncio.sleep(settings.chain_refresh_interval)

        if not _watched_symbols:
            continue

        logger.info(f"Refreshing {len(_watched_symbols)} symbols...")
        provider = get_provider()

        for symbol in list(_watched_symbols):
            try:
                expiries = await provider.get_expiries(symbol)
                if not expiries:
                    continue

                # Refresh nearest 3 expiries
                for expiry in expiries[:3]:
                    contracts = await provider.get_option_chain(symbol, expiry)
                    quote     = await provider.get_quote(symbol)
                    enriched  = enrich_chain(contracts, quote.price, settings.risk_free_rate, 0.0)

                    async with db_session_factory() as db:
                        await store_chain_snapshot(db, symbol, expiry, enriched, quote.price)

                    logger.info(f"Refreshed {symbol} {expiry} — {len(enriched)} contracts")

            except Exception as e:
                logger.warning(f"Failed to refresh {symbol}: {e}")
