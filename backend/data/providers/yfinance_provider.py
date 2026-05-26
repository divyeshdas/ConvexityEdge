"""
yfinance-backed implementation of MarketDataProvider.

Uses yfinance for quotes, OHLC, and options chain data.
Runs in an async thread pool to avoid blocking the FastAPI event loop
(yfinance is synchronous under the hood).
"""

import asyncio
import datetime
from typing import Optional
import yfinance as yf
import pandas as pd

from data.providers.base import (
    MarketDataProvider,
    QuoteData,
    OHLCBar,
    OptionContractData,
)

# yfinance period/interval strings supported
VALID_PERIODS   = {"1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"}
VALID_INTERVALS = {"1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"}

_EXECUTOR = None  # shared thread-pool executor


def _run_sync(fn):
    """Run a synchronous callable in the default thread pool."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, fn)


class YFinanceProvider(MarketDataProvider):

    async def get_quote(self, symbol: str) -> QuoteData:
        def _fetch():
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            hist = ticker.history(period="2d", interval="1d")

            price      = float(info.last_price or 0)
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            change     = price - prev_close
            change_pct = (change / prev_close) if prev_close else 0.0
            volume     = int(info.three_month_average_volume or 0)
            mkt_cap    = float(info.market_cap) if hasattr(info, 'market_cap') and info.market_cap else None

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
            ticker = yf.Ticker(symbol)
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
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                ))
            return bars

        return await _run_sync(_fetch)

    async def get_expiries(self, symbol: str) -> list[datetime.date]:
        def _fetch():
            ticker = yf.Ticker(symbol)
            raw = ticker.options  # tuple of date strings "YYYY-MM-DD"
            return [datetime.date.fromisoformat(d) for d in raw]

        return await _run_sync(_fetch)

    async def get_option_chain(
        self,
        symbol: str,
        expiry: datetime.date,
    ) -> list[OptionContractData]:
        expiry_str = expiry.isoformat()

        def _fetch():
            ticker = yf.Ticker(symbol)
            chain  = ticker.option_chain(expiry_str)

            contracts: list[OptionContractData] = []

            def _parse(df: pd.DataFrame, option_type: str):
                for _, row in df.iterrows():
                    contracts.append(OptionContractData(
                        symbol=symbol.upper(),
                        option_type=option_type,
                        strike=float(row.get("strike", 0)),
                        expiry=expiry,
                        bid=float(row.get("bid", 0) or 0),
                        ask=float(row.get("ask", 0) or 0),
                        last=float(row.get("lastPrice", 0) or 0),
                        volume=int(row.get("volume", 0) or 0),
                        open_interest=int(row.get("openInterest", 0) or 0),
                        implied_vol=float(row.get("impliedVolatility", 0) or 0) or None,
                    ))

            _parse(chain.calls, "C")
            _parse(chain.puts,  "P")
            return contracts

        return await _run_sync(_fetch)

    async def search_symbols(self, query: str) -> list[dict]:
        """
        yfinance doesn't have a built-in symbol search endpoint.
        We check against the seeded symbol list and do a simple
        prefix/substring match. A production provider (Polygon, Alpaca)
        would hit a proper search API here.
        """
        KNOWN_SYMBOLS = [
            {"ticker": "AAPL",  "name": "Apple Inc.",                     "exchange": "NASDAQ", "asset_type": "equity"},
            {"ticker": "MSFT",  "name": "Microsoft Corporation",           "exchange": "NASDAQ", "asset_type": "equity"},
            {"ticker": "AMZN",  "name": "Amazon.com Inc.",                 "exchange": "NASDAQ", "asset_type": "equity"},
            {"ticker": "NVDA",  "name": "NVIDIA Corporation",              "exchange": "NASDAQ", "asset_type": "equity"},
            {"ticker": "GOOGL", "name": "Alphabet Inc.",                   "exchange": "NASDAQ", "asset_type": "equity"},
            {"ticker": "META",  "name": "Meta Platforms Inc.",             "exchange": "NASDAQ", "asset_type": "equity"},
            {"ticker": "TSLA",  "name": "Tesla Inc.",                      "exchange": "NASDAQ", "asset_type": "equity"},
            {"ticker": "SPY",   "name": "SPDR S&P 500 ETF Trust",          "exchange": "NYSE",   "asset_type": "etf"},
            {"ticker": "QQQ",   "name": "Invesco QQQ Trust",               "exchange": "NASDAQ", "asset_type": "etf"},
            {"ticker": "IWM",   "name": "iShares Russell 2000 ETF",        "exchange": "NYSE",   "asset_type": "etf"},
            {"ticker": "GLD",   "name": "SPDR Gold Shares",                "exchange": "NYSE",   "asset_type": "etf"},
            {"ticker": "TLT",   "name": "iShares 20+ Year Treasury Bond",  "exchange": "NASDAQ", "asset_type": "etf"},
        ]
        q = query.upper()
        return [
            s for s in KNOWN_SYMBOLS
            if q in s["ticker"] or q in s["name"].upper()
        ][:10]
