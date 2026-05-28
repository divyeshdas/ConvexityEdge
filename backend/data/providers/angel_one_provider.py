"""
Angel One SmartAPI-backed provider for NSE F&O data.
"""

import asyncio
import datetime
import logging

import pyotp

from app.core.config import settings
from data.providers.base import OptionContractData, OHLCBar, QuoteData
from data.providers.yfinance_provider import YFinanceProvider, _ff, _fi, _run_sync

logger = logging.getLogger(__name__)

_INTERVAL_MAP = {
    "1m": "ONE_MINUTE", "5m": "FIVE_MINUTE", "15m": "FIFTEEN_MINUTE",
    "30m": "THIRTY_MINUTE", "60m": "ONE_HOUR", "1h": "ONE_HOUR",
    "1d": "ONE_DAY", "1wk": "ONE_WEEK", "1mo": "ONE_MONTH",
}

_PERIOD_DAYS = {
    "1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
    "1y": 365, "2y": 730, "5y": 1825, "ytd": 180, "max": 1825,
}

_INST_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"


def _make_sdk():
    from SmartApi import SmartConnect
    return SmartConnect(api_key=settings.angel_one_api_key)


class AngelOneProvider(YFinanceProvider):

    def __init__(self):
        super().__init__()
        self._obj = None
        self._session_valid = False
        self._auth_lock  = asyncio.Lock()
        self._instr_lock = asyncio.Lock()
        self._instruments: list[dict] = []
        self._instr_loaded = False

    # ── Authentication ────────────────────────────────────────────────────────

    def _do_login(self):
        if self._obj is None:
            self._obj = _make_sdk()
        totp = pyotp.TOTP(settings.angel_one_totp_secret).now()
        resp = self._obj.generateSession(
            settings.angel_one_client_code,
            settings.angel_one_password,
            totp,
        )
        if not resp.get("status"):
            raise RuntimeError(f"Angel One login failed: {resp.get('message', resp)}")
        self._session_valid = True
        logger.info("Angel One session refreshed")

    async def _ensure_auth(self):
        if self._session_valid:
            return
        async with self._auth_lock:
            if self._session_valid:
                return
            await _run_sync(self._do_login)

    async def _force_reauth(self):
        """Invalidate session and re-login. Called when an API returns status=False."""
        self._session_valid = False
        async with self._auth_lock:
            await _run_sync(self._do_login)

    # ── Instrument master ─────────────────────────────────────────────────────

    def _load_instruments(self):
        import urllib.request, json
        with urllib.request.urlopen(_INST_URL, timeout=60) as r:
            self._instruments = json.loads(r.read().decode())
        self._instr_loaded = True

    async def _ensure_instruments(self):
        if self._instr_loaded:
            return
        async with self._instr_lock:
            if self._instr_loaded:
                return
            await _run_sync(self._load_instruments)

    # ── Equity token lookup ───────────────────────────────────────────────────

    def _find_nse_equity_token(self, symbol: str) -> str | None:
        """Find NSE equity token. Matches on symbol field (most reliable for equities)."""
        sym = symbol.upper()
        for entry in self._instruments:
            if entry.get("exch_seg") != "NSE":
                continue
            # NSE equities: instrumenttype is "" or "EQ"
            if entry.get("instrumenttype", "") not in ("", "EQ"):
                continue
            if entry.get("symbol", "").upper() == sym or entry.get("name", "").upper() == sym:
                token = entry.get("token", "")
                if token:
                    return token
        return None

    # ── Provider interface ────────────────────────────────────────────────────

    async def get_quote(self, symbol: str) -> QuoteData:
        try:
            await self._ensure_auth()
            await self._ensure_instruments()
        except Exception as exc:
            logger.warning("Angel One init failed for get_quote(%s), falling back: %s", symbol, exc)
            return await super().get_quote(symbol)

        token = self._find_nse_equity_token(symbol)
        if not token:
            logger.warning("No NSE equity token for %s, falling back to yfinance", symbol)
            return await super().get_quote(symbol)

        for attempt in range(2):
            try:
                def _fetch():
                    result = self._obj.getMarketData("FULL", {"NSE": [token]})
                    return result

                result = await _run_sync(_fetch)
            except Exception as exc:
                logger.warning("getMarketData raised for %s: %s", symbol, exc)
                if attempt == 0:
                    await self._force_reauth()
                continue

            if result.get("status"):
                fetched = (result.get("data") or {}).get("fetched") or []
                if fetched:
                    md = fetched[0]
                    ltp   = _ff(md.get("ltp"))
                    close = _ff(md.get("close"))
                    change     = ltp - close
                    change_pct = (change / close) if close else 0.0
                    return QuoteData(
                        symbol=symbol.upper(),
                        price=ltp,
                        change=change,
                        change_pct=change_pct,
                        volume=_fi(md.get("tradeVolume")),
                        market_cap=None,
                        timestamp=datetime.datetime.utcnow(),
                    )
            # status=False → session likely expired, re-auth and retry
            if attempt == 0:
                logger.warning("getMarketData failed for %s, re-authenticating...", symbol)
                await self._force_reauth()

        logger.warning("getMarketData failed after reauth for %s, falling back", symbol)
        return await super().get_quote(symbol)

    async def get_ohlc(self, symbol: str, period: str = "3mo", interval: str = "1d") -> list[OHLCBar]:
        try:
            await self._ensure_auth()
            await self._ensure_instruments()
        except Exception as exc:
            logger.warning("Angel One init failed for get_ohlc(%s), falling back: %s", symbol, exc)
            return await super().get_ohlc(symbol, period, interval)

        token = self._find_nse_equity_token(symbol)
        if not token:
            return await super().get_ohlc(symbol, period, interval)

        ao_interval = _INTERVAL_MAP.get(interval, "ONE_DAY")
        days = _PERIOD_DAYS.get(period, 90)
        today = datetime.datetime.now()
        fromdate = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d 09:15")
        todate = today.strftime("%Y-%m-%d 15:30")

        for attempt in range(2):
            def _fetch():
                return self._obj.getCandleData({
                    "exchange": "NSE",
                    "symboltoken": token,
                    "interval": ao_interval,
                    "fromdate": fromdate,
                    "todate": todate,
                })

            result = await _run_sync(_fetch)
            if result.get("status"):
                rows = result.get("data") or []
                bars = []
                for row in rows:
                    try:
                        ts = datetime.datetime.fromisoformat(row[0].replace("T", " ").split("+")[0])
                        bars.append(OHLCBar(
                            time=ts,
                            open=_ff(row[1]), high=_ff(row[2]),
                            low=_ff(row[3]),  close=_ff(row[4]),
                            volume=_fi(row[5]),
                        ))
                    except Exception:
                        continue
                return bars

            if attempt == 0:
                logger.warning("getCandleData failed for %s, re-authenticating...", symbol)
                await self._force_reauth()

        return await super().get_ohlc(symbol, period, interval)

    async def get_expiries(self, symbol: str) -> list[datetime.date]:
        try:
            await self._ensure_instruments()
        except Exception as exc:
            logger.warning("Angel One instrument load failed for get_expiries(%s): %s", symbol, exc)
            return []
        today = datetime.date.today()
        seen: set[str] = set()
        dates: list[datetime.date] = []

        for entry in self._instruments:
            if (
                entry.get("name", "").upper() == symbol.upper() and
                entry.get("instrumenttype") in ("OPTSTK", "OPTIDX") and
                entry.get("exch_seg") == "NFO"
            ):
                raw = entry.get("expiry", "")
                if raw and raw not in seen:
                    try:
                        expiry = datetime.datetime.strptime(raw.title(), "%d%b%Y").date()
                        if expiry >= today:
                            seen.add(raw)
                            dates.append(expiry)
                    except ValueError:
                        pass

        return sorted(dates)

    async def get_option_chain(
        self,
        symbol: str,
        expiry: datetime.date,
    ) -> list[OptionContractData]:
        try:
            await self._ensure_auth()
            await self._ensure_instruments()
        except Exception as exc:
            logger.warning("Angel One init failed for get_option_chain(%s), returning empty: %s", symbol, exc)
            return []

        # Build token lookup from instrument master
        token_map: dict[tuple[float, str], str] = {}
        for entry in self._instruments:
            if (
                entry.get("name", "").upper() == symbol.upper() and
                entry.get("instrumenttype") in ("OPTSTK", "OPTIDX") and
                entry.get("exch_seg") == "NFO"
            ):
                raw = entry.get("expiry", "")
                try:
                    ent_exp = datetime.datetime.strptime(raw.title(), "%d%b%Y").date()
                except ValueError:
                    continue
                if ent_exp != expiry:
                    continue
                sym_str = entry.get("symbol", "")
                otype = "CE" if sym_str.endswith("CE") else "PE"
                try:
                    strike = float(entry.get("strike", 0)) / 100.0
                except (TypeError, ValueError):
                    continue
                token_map[(strike, otype)] = entry.get("token", "")

        tokens = [t for t in token_map.values() if t]

        # Fetch market data with re-auth retry
        md_map: dict[str, dict] = {}
        for attempt in range(2):
            md_map = {}
            failed = False
            for i in range(0, len(tokens), 50):
                batch = tokens[i : i + 50]

                def _fetch_md(b=batch):
                    return self._obj.getMarketData("FULL", {"NFO": b})

                result = await _run_sync(_fetch_md)
                if not result.get("status"):
                    failed = True
                    break
                for item in (result.get("data", {}).get("fetched") or []):
                    tok = str(item.get("symbolToken", ""))
                    if tok:
                        md_map[tok] = item

            if not failed:
                break
            if attempt == 0:
                logger.warning("getMarketData (NFO) failed, re-authenticating...")
                await self._force_reauth()

        contracts: list[OptionContractData] = []
        for (strike, otype), token in token_map.items():
            md    = md_map.get(token, {})
            depth = md.get("depth") or {}
            bid   = _ff((depth.get("buy")  or [{}])[0].get("price"))
            ask   = _ff((depth.get("sell") or [{}])[0].get("price"))
            ltp   = _ff(md.get("ltp"))

            contracts.append(OptionContractData(
                symbol=symbol.upper(),
                option_type="C" if otype == "CE" else "P",
                strike=strike,
                expiry=expiry,
                bid=bid,
                ask=ask,
                last=ltp,
                volume=_fi(md.get("tradeVolume")),
                open_interest=_fi(md.get("opnInterest")),
                implied_vol=None,
            ))

        return contracts
