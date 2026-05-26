from fastapi import APIRouter, Query
from data.pipeline import get_provider

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    provider = get_provider()
    q = await provider.get_quote(symbol.upper())
    return {
        "symbol":     q.symbol,
        "price":      round(q.price, 4),
        "change":     round(q.change, 4),
        "change_pct": round(q.change_pct, 6),
        "volume":     q.volume,
        "market_cap": q.market_cap,
        "timestamp":  q.timestamp.isoformat(),
    }


@router.get("/chart/{symbol}")
async def get_chart(
    symbol: str,
    period:   str = Query("3mo"),
    interval: str = Query("1d"),
):
    provider = get_provider()
    bars = await provider.get_ohlc(symbol.upper(), period=period, interval=interval)
    return [
        {
            "time":   int(b.time.timestamp()),
            "open":   round(b.open, 4),
            "high":   round(b.high, 4),
            "low":    round(b.low, 4),
            "close":  round(b.close, 4),
            "volume": b.volume,
        }
        for b in bars
    ]
