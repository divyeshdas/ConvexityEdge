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
        self._instr_loaded = False

        # Fast lookup structures built during _load_instruments
        # NSE equity: symbol_upper / name_upper → token
        self._equity_tokens: dict[str, str] = {}
        # NFO options: name_upper → list of (expiry_date, strike, otype, token)
        self._nfo_options: dict[str, list[tuple]] = {}

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
        self._session_valid = False
        async with self._auth_lock:
            await _run_sync(self._do_login)

    # ── Instrument master ─────────────────────────────────────────────────────

    def _load_instruments(self):
        import urllib.request, json
        with urllib.request.urlopen(_INST_URL, timeout=60) as r:
            raw: list[dict] = json.loads(r.read().decode())

        equity: dict[str, str] = {}
        nfo: dict[str, list] = {}

        for entry in raw:
            seg  = entry.get("exch_seg", "")
            itype = entry.get("instrumenttype", "")
            token = entry.get("token", "")
            if not token:
                continue

            if seg == "NSE" and itype in ("", "EQ"):
                sym  = entry.get("symbol", "").upper()
                name = entry.get("name",   "").upper()
                if sym:
                    equity[sym] = token
                if name:
                    equity.setdefault(name, token)

            elif seg == "NFO" and itype in ("OPTSTK", "OPTIDX"):
                name = entry.get("name", "").upper()
                raw_exp = entry.get("expiry", "")
                sym_str = entry.get("symbol", "")
                try:
                    exp = datetime.datetime.strptime(raw_exp.title(), "%d%b%Y").date()
                    strike = float(entry.get("strike", 0)) / 100.0
                except (ValueError, TypeError):
                    continue
                otype = "CE" if sym_str.endswith("CE") else "PE"
                nfo.setdefault(name, []).append((exp, strike, otype, token))

        self._equity_tokens = equity
        self._nfo_options   = nfo
        self._instr_loaded  = True
        logger.info(
            "Instrument master loaded: %d equity tokens, %d NFO symbols",
            len(equity), len(nfo),
        )

    async def _ensure_instruments(self):
        if self._instr_loaded:
            return
        async with self._instr_lock:
            if self._instr_loaded:
                return
            await _run_sync(self._load_instruments)

    # ── Equity token lookup — O(1) ────────────────────────────────────────────

    def _find_nse_equity_token(self, symbol: str) -> str | None:
        return self._equity_tokens.get(symbol.upper())

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
            return await super().get_quote(symbol)

        for attempt in range(2):
            try:
                def _fetch(t=token):
                    return self._obj.getMarketData("FULL", {"NSE": [t]})
                result = await _run_sync(_fetch)
            except Exception as exc:
                logger.warning("getMarketData raised for %s: %s", symbol, exc)
                if attempt == 0:
                    await self._force_reauth()
                continue

            if result.get("status"):
                fetched = (result.get("data") or {}).get("fetched") or []
                if fetched:
                    md     = fetched[0]
                    ltp    = _ff(md.get("ltp"))
                    close  = _ff(md.get("close"))
                    change = ltp - close
                    return QuoteData(
                        symbol=symbol.upper(),
                        price=ltp,
                        change=change,
                        change_pct=(change / close) if close else 0.0,
                        volume=_fi(md.get("tradeVolume")),
                        market_cap=None,
                        timestamp=datetime.datetime.utcnow(),
                    )
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
        todate   = today.strftime("%Y-%m-%d 15:30")

        for attempt in range(2):
            try:
                def _fetch(t=token, fi=ao_interval, fd=fromdate, td=todate):
                    return self._obj.getCandleData({
                        "exchange": "NSE", "symboltoken": t,
                        "interval": fi, "fromdate": fd, "todate": td,
                    })
                result = await _run_sync(_fetch)
            except Exception as exc:
                logger.warning("getCandleData raised for %s: %s", symbol, exc)
                if attempt == 0:
                    await self._force_reauth()
                continue

            if result.get("status"):
                bars = []
                for row in result.get("data") or []:
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
            logger.warning("Instrument load failed for get_expiries(%s): %s", symbol, exc)
            return []

        today   = datetime.date.today()
        entries = self._nfo_options.get(symbol.upper(), [])
        dates   = sorted({exp for exp, _, _, _ in entries if exp >= today})
        return dates

    async def get_option_chain(
        self,
        symbol: str,
        expiry: datetime.date,
    ) -> list[OptionContractData]:
        try:
            await self._ensure_auth()
            await self._ensure_instruments()
        except Exception as exc:
            logger.warning("Angel One init failed for get_option_chain(%s): %s", symbol, exc)
            return []

        # O(k) filter from pre-indexed NFO options
        entries = self._nfo_options.get(symbol.upper(), [])
        token_map: dict[tuple[float, str], str] = {
            (strike, otype): token
            for exp, strike, otype, token in entries
            if exp == expiry and token
        }
        tokens = list(token_map.values())

        if not tokens:
            return []

        # Fetch all batches in parallel — typically 4-6 batches of 50
        batches = [tokens[i : i + 50] for i in range(0, len(tokens), 50)]

        async def _fetch_batch(batch: list[str]) -> dict:
            def _call(b=batch):
                return self._obj.getMarketData("FULL", {"NFO": b})
            return await _run_sync(_call)

        md_map: dict[str, dict] = {}
        for attempt in range(2):
            try:
                results = await asyncio.gather(*[_fetch_batch(b) for b in batches])
            except Exception as exc:
                logger.warning("getMarketData gather failed attempt %d: %s", attempt, exc)
                if attempt == 0:
                    await self._force_reauth()
                continue

            failed = any(not r.get("status") for r in results)
            if failed and attempt == 0:
                logger.warning("getMarketData (NFO) had failures, re-authenticating...")
                await self._force_reauth()
                continue

            md_map = {}
            for r in results:
                for item in (r.get("data", {}).get("fetched") or []):
                    tok = str(item.get("symbolToken", ""))
                    if tok:
                        md_map[tok] = item
            break

        contracts: list[OptionContractData] = []
        for (strike, otype), token in token_map.items():
            md    = md_map.get(token, {})
            depth = md.get("depth") or {}
            bid   = _ff((depth.get("buy")  or [{}])[0].get("price"))
            ask   = _ff((depth.get("sell") or [{}])[0].get("price"))
            contracts.append(OptionContractData(
                symbol=symbol.upper(),
                option_type="C" if otype == "CE" else "P",
                strike=strike,
                expiry=expiry,
                bid=bid,
                ask=ask,
                last=_ff(md.get("ltp")),
                volume=_fi(md.get("tradeVolume")),
                open_interest=_fi(md.get("opnInterest")),
                implied_vol=None,
            ))

        return contracts
