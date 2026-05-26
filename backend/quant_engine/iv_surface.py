"""
IV surface construction: smile, skew, term structure, and 3D surface.

All functions accept lists of solved IV data points (from iv_solver)
and return structured data ready for frontend chart consumption.
"""

import numpy as np
from typing import Optional


def build_iv_smile(
    strikes: list[float],
    ivs: list[float],
    option_types: list[str],
    underlying: float,
) -> list[dict]:
    """
    IV Smile: IV plotted against strike for a single expiry.
    Points sorted by strike ascending.
    Moneyness = ln(K/S) — negative = OTM put, 0 = ATM, positive = OTM call.
    """
    points = []
    for K, iv, ot in zip(strikes, ivs, option_types):
        if iv is None or iv <= 0:
            continue
        moneyness = np.log(K / underlying) if underlying > 0 else 0.0
        points.append({
            "strike":      round(K, 4),
            "iv":          round(iv, 6),
            "iv_pct":      round(iv * 100, 2),
            "moneyness":   round(float(moneyness), 4),
            "option_type": ot.upper(),
        })
    return sorted(points, key=lambda x: x["strike"])


def build_iv_skew(
    strikes: list[float],
    ivs: list[float],
    option_types: list[str],
    underlying: float,
) -> list[dict]:
    """
    IV Skew: difference between each point's IV and the ATM IV.
    ATM is the strike closest to underlying. Skew > 0 = higher than ATM.
    """
    smile = build_iv_smile(strikes, ivs, option_types, underlying)
    if not smile:
        return []

    atm = min(smile, key=lambda p: abs(p["strike"] - underlying))
    atm_iv = atm["iv"]

    return [
        {**p, "skew": round(p["iv"] - atm_iv, 6), "skew_pct": round((p["iv"] - atm_iv) * 100, 2)}
        for p in smile
    ]


def build_iv_term_structure(
    expiries: list[str],
    dtes: list[int],
    atm_ivs: list[float],
) -> list[dict]:
    """
    IV Term Structure: ATM IV vs days-to-expiry across all expiries.
    Points sorted by DTE ascending.
    """
    points = []
    for exp, dte, iv in zip(expiries, dtes, atm_ivs):
        if iv is None or iv <= 0:
            continue
        points.append({
            "expiry":  exp,
            "dte":     dte,
            "atm_iv":  round(iv, 6),
            "iv_pct":  round(iv * 100, 2),
        })
    return sorted(points, key=lambda x: x["dte"])


def build_iv_surface(
    strikes: list[float],
    dtes: list[int],
    ivs: list[float],
    underlying: float,
) -> list[dict]:
    """
    IV Surface: 3D mesh of (strike, DTE, IV).
    Used for ECharts 3D surface chart.
    """
    points = []
    for K, dte, iv in zip(strikes, dtes, ivs):
        if iv is None or iv <= 0:
            continue
        moneyness = np.log(K / underlying) if underlying > 0 else 0.0
        points.append({
            "strike":    round(K, 4),
            "dte":       dte,
            "iv":        round(iv, 6),
            "iv_pct":    round(iv * 100, 2),
            "moneyness": round(float(moneyness), 4),
        })
    return points


def compute_atm_iv(
    strikes: list[float],
    ivs: list[float],
    underlying: float,
) -> Optional[float]:
    """
    Find the IV of the strike closest to the underlying price.
    Returns None if no valid IV points.
    """
    valid = [(K, iv) for K, iv in zip(strikes, ivs) if iv and iv > 0]
    if not valid:
        return None
    atm_strike, atm_iv = min(valid, key=lambda x: abs(x[0] - underlying))
    return round(atm_iv, 6)


def compute_iv_rank(
    current_iv: float,
    iv_history: list[float],
) -> Optional[float]:
    """
    IV Rank: where current IV sits in its 52-week range.
    IV Rank = (current - min) / (max - min) × 100
    Returns 0-100 scale. None if insufficient history.
    """
    hist = [v for v in iv_history if v and v > 0]
    if len(hist) < 5:
        return None
    iv_min = min(hist)
    iv_max = max(hist)
    if iv_max <= iv_min:
        return 50.0
    rank = (current_iv - iv_min) / (iv_max - iv_min) * 100
    return round(max(0.0, min(100.0, rank)), 1)


def compute_historical_vol(prices: list[float], window: int = 30) -> Optional[float]:
    """
    30-day historical (realised) volatility using close-to-close log returns.
    Annualised with √252 (trading days).
    Returns None if insufficient data.
    """
    if len(prices) < window + 1:
        return None
    prices_arr = np.array(prices[-window - 1:], dtype=float)
    log_returns = np.diff(np.log(prices_arr))
    if len(log_returns) < 2:
        return None
    hv = float(np.std(log_returns, ddof=1) * np.sqrt(252))
    return round(hv, 6)
