"""
Abstract base class for all market data providers.

To add a new data source (Zerodha, Alpaca, Breeze, etc.):
1. Create a new file in data/providers/
2. Subclass MarketDataProvider
3. Implement all abstract methods
4. Update PROVIDER_MAP in data/pipeline.py

No other code needs to change.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import datetime


@dataclass
class QuoteData:
    symbol:        str
    price:         float
    change:        float
    change_pct:    float
    volume:        int
    market_cap:    Optional[float]
    timestamp:     datetime.datetime


@dataclass
class OHLCBar:
    time:    datetime.datetime
    open:    float
    high:    float
    low:     float
    close:   float
    volume:  int


@dataclass
class OptionContractData:
    symbol:        str
    option_type:   str   # 'C' or 'P'
    strike:        float
    expiry:        datetime.date
    bid:           float
    ask:           float
    last:          float
    volume:        int
    open_interest: int
    implied_vol:   Optional[float]   # market-reported IV if available


class MarketDataProvider(ABC):

    @abstractmethod
    async def get_quote(self, symbol: str) -> QuoteData:
        """Fetch current price and basic quote for a symbol."""
        ...

    @abstractmethod
    async def get_ohlc(
        self,
        symbol: str,
        period: str = "3mo",
        interval: str = "1d",
    ) -> list[OHLCBar]:
        """Fetch historical OHLC bars for chart display."""
        ...

    @abstractmethod
    async def get_expiries(self, symbol: str) -> list[datetime.date]:
        """Return all available option expiry dates for a symbol."""
        ...

    @abstractmethod
    async def get_option_chain(
        self,
        symbol: str,
        expiry: datetime.date,
    ) -> list[OptionContractData]:
        """
        Return all option contracts for a given symbol and expiry.
        Includes bid, ask, last, volume, open_interest.
        IV is optional — if None, the engine will solve it from the price.
        """
        ...

    @abstractmethod
    async def search_symbols(self, query: str) -> list[dict]:
        """Return list of {ticker, name, exchange, asset_type} matching query."""
        ...

    async def get_close_prices(
        self,
        symbol: str,
        days: int = 60,
    ) -> list[float]:
        """
        Convenience: return closing prices for historical volatility calculation.
        Default implementation uses get_ohlc; providers can override for efficiency.
        """
        bars = await self.get_ohlc(symbol, period=f"{days}d", interval="1d")
        return [b.close for b in bars]
