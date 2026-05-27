"""
yfinance-backed implementation of MarketDataProvider — Indian NSE edition.

Fetches NSE-listed equity quotes, OHLC, and options chain data.
Symbols are stored without exchange suffix (e.g. "RELIANCE"); the provider
appends ".NS" internally when calling yfinance so the rest of the app
never has to know about exchange suffixes.
"""

import asyncio
import datetime
import math
from typing import Optional
import yfinance as yf
import pandas as pd


def _fi(val, default: int = 0) -> int:
    """float-safe int: returns default for NaN/None/inf."""
    try:
        v = float(val)
        return default if (math.isnan(v) or math.isinf(v)) else int(v)
    except (TypeError, ValueError):
        return default


def _ff(val, default: float = 0.0) -> float:
    """float-safe float: returns default for NaN/None/inf."""
    try:
        v = float(val)
        return default if (math.isnan(v) or math.isinf(v)) else v
    except (TypeError, ValueError):
        return default

from data.providers.base import (
    MarketDataProvider,
    QuoteData,
    OHLCBar,
    OptionContractData,
)

VALID_PERIODS   = {"1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"}
VALID_INTERVALS = {"1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"}


def _nse(symbol: str) -> str:
    """Append NSE suffix for yfinance if not already present."""
    s = symbol.upper()
    if s.endswith('.NS') or s.endswith('.BO'):
        return s
    return f"{s}.NS"


def _run_sync(fn):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, fn)


class YFinanceProvider(MarketDataProvider):

    async def get_quote(self, symbol: str) -> QuoteData:
        def _fetch():
            ticker = yf.Ticker(_nse(symbol))
            info   = ticker.fast_info
            hist   = ticker.history(period="2d", interval="1d")

            price      = _ff(info.last_price)
            prev_close = _ff(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            change     = price - prev_close
            change_pct = (change / prev_close) if prev_close else 0.0
            volume     = _fi(getattr(info, 'three_month_average_volume', 0))
            mkt_cap    = _ff(getattr(info, 'market_cap', None)) or None

            return QuoteData(
                symbol=symbol.upper(),
                price=price,
                change=change,
                change_pct=change_pct,
                volume=volume,
                market_cap=mkt_cap,
                timestamp=datetime.datetime.utcnow(),
            )

        return await _run_sync(_fetch)

    async def get_ohlc(
        self,
        symbol: str,
        period: str = "3mo",
        interval: str = "1d",
    ) -> list[OHLCBar]:
        period   = period   if period   in VALID_PERIODS   else "3mo"
        interval = interval if interval in VALID_INTERVALS else "1d"

        def _fetch():
            ticker = yf.Ticker(_nse(symbol))
            hist = ticker.history(period=period, interval=interval)
            bars = []
            for ts, row in hist.iterrows():
                # pandas Timestamp → python datetime
                if hasattr(ts, 'to_pydatetime'):
                    dt = ts.to_pydatetime().replace(tzinfo=None)
                else:
                    dt = datetime.datetime.utcfromtimestamp(ts)
                bars.append(OHLCBar(
                    time=dt,
                    open=_ff(row["Open"]),
                    high=_ff(row["High"]),
                    low=_ff(row["Low"]),
                    close=_ff(row["Close"]),
                    volume=_fi(row["Volume"]),
                ))
            return bars

        return await _run_sync(_fetch)

    async def get_expiries(self, symbol: str) -> list[datetime.date]:
        def _fetch():
            ticker = yf.Ticker(_nse(symbol))
            return [datetime.date.fromisoformat(d) for d in ticker.options]

        return await _run_sync(_fetch)

    async def get_option_chain(
        self,
        symbol: str,
        expiry: datetime.date,
    ) -> list[OptionContractData]:
        expiry_str = expiry.isoformat()

        def _fetch():
            ticker = yf.Ticker(_nse(symbol))
            chain  = ticker.option_chain(expiry_str)

            contracts: list[OptionContractData] = []

            def _parse(df: pd.DataFrame, option_type: str):
                for _, row in df.iterrows():
                    iv = _ff(row.get("impliedVolatility"))
                    contracts.append(OptionContractData(
                        symbol=symbol.upper(),
                        option_type=option_type,
                        strike=_ff(row.get("strike")),
                        expiry=expiry,
                        bid=_ff(row.get("bid")),
                        ask=_ff(row.get("ask")),
                        last=_ff(row.get("lastPrice")),
                        volume=_fi(row.get("volume")),
                        open_interest=_fi(row.get("openInterest")),
                        implied_vol=iv if iv > 0 else None,
                    ))

            _parse(chain.calls, "C")
            _parse(chain.puts,  "P")
            return contracts

        return await _run_sync(_fetch)

    async def search_symbols(self, query: str) -> list[dict]:
        # NSE F&O stocks with active options markets
        KNOWN_SYMBOLS = [
            {"ticker": "RELIANCE",    "name": "Reliance Industries Ltd",          "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "TCS",         "name": "Tata Consultancy Services Ltd",    "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "INFY",        "name": "Infosys Ltd",                      "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "HDFCBANK",    "name": "HDFC Bank Ltd",                    "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "ICICIBANK",   "name": "ICICI Bank Ltd",                   "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "SBIN",        "name": "State Bank of India",              "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "BAJFINANCE",  "name": "Bajaj Finance Ltd",                "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "WIPRO",       "name": "Wipro Ltd",                        "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "AXISBANK",    "name": "Axis Bank Ltd",                    "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "KOTAKBANK",   "name": "Kotak Mahindra Bank Ltd",          "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "TATAMOTORS",  "name": "Tata Motors Ltd",                  "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "MARUTI",      "name": "Maruti Suzuki India Ltd",          "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "SUNPHARMA",   "name": "Sun Pharmaceutical Industries",    "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "HINDUNILVR",  "name": "Hindustan Unilever Ltd",           "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "ITC",         "name": "ITC Ltd",                          "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "ONGC",        "name": "Oil and Natural Gas Corp",         "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "NTPC",        "name": "NTPC Ltd",                         "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "POWERGRID",   "name": "Power Grid Corp of India",         "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "ADANIENT",    "name": "Adani Enterprises Ltd",            "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "ADANIPORTS",  "name": "Adani Ports and SEZ Ltd",          "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "TATASTEEL",   "name": "Tata Steel Ltd",                   "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "JSWSTEEL",    "name": "JSW Steel Ltd",                    "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "HCLTECH",     "name": "HCL Technologies Ltd",             "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "TECHM",       "name": "Tech Mahindra Ltd",                "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "LTIM",        "name": "LTIMindtree Ltd",                  "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "BAJAJFINSV",  "name": "Bajaj Finserv Ltd",                "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "ASIANPAINT",  "name": "Asian Paints Ltd",                 "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "ULTRACEMCO",  "name": "UltraTech Cement Ltd",             "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "NESTLEIND",   "name": "Nestle India Ltd",                 "exchange": "NSE", "asset_type": "equity"},
            {"ticker": "TITAN",       "name": "Titan Company Ltd",                "exchange": "NSE", "asset_type": "equity"},
        ]
        q = query.upper()
        return [
            s for s in KNOWN_SYMBOLS
            if q in s["ticker"] or q in s["name"].upper()
        ][:10]
